"""Admin controls must be protected, durable, and connected to actual execution."""
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.database import Base
from app.models.user import User, UserUsage, VerifiedWhatsAppAccount
from app.models.onboarding import UserOnboarding
from app.routes import admin, admin_portal


class AdminPortalTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from app.services import runtime
        self.runtime = runtime
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.patches = [patch.object(admin, "async_session", self.sessions),
                        patch.object(admin_portal, "async_session", self.sessions),
                        patch.object(runtime, "async_session", self.sessions),
                        patch.object(runtime, "ensure_tables", AsyncMock()),
                        patch.object(admin.settings, "ADMIN_API_KEY", "test-admin-key-" + "x" * 40)]
        for item in self.patches:
            item.start()
        app = FastAPI()
        app.include_router(admin.router)
        app.include_router(admin_portal.router)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
        self.headers = {"X-Admin-Key": admin.settings.ADMIN_API_KEY}

    async def asyncTearDown(self):
        await self.client.aclose()
        for item in reversed(self.patches):
            item.stop()
        await self.engine.dispose()

    async def test_admin_endpoints_fail_closed(self):
        for path in ("overview", "users", "analytics", "config", "audit", "models"):
            self.assertEqual((await self.client.get(f"/api/admin/{path}")).status_code, 403)
            self.assertEqual((await self.client.get(f"/api/admin/{path}", headers={"X-Admin-Key": "wrong"})).status_code, 403)

    async def test_lifecycle_and_usage_are_real_records(self):
        async with self.sessions() as db:
            user = User(phone_number="919123456789", name="Astra Test")
            db.add(user)
            await db.flush()
            db.add(UserOnboarding(user_id=user.id, step="complete", completed_at=datetime.utcnow()))
            db.add(UserUsage(user_id=user.id, date=date.today(), query_count=3))
            await db.commit()
        response = await self.client.get("/api/admin/users?q=Astra", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["items"][0]["stage"], "active")
        self.assertEqual(response.json()["items"][0]["used_today"], 3)
        self.assertEqual((await self.client.get("/api/admin/overview", headers=self.headers)).json()["today_queries"], 3)

    async def test_config_validation_concurrency_audit_and_live_routing(self):
        config = (await self.client.get("/api/admin/config", headers=self.headers)).json()
        payload = {"revision": config["revision"], "values": {"FREE_DAILY_LIMIT": 9, "reply_model": "gemini-3.5-flash-lite"}}
        saved = await self.client.patch("/api/admin/config", headers=self.headers, json=payload)
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual((await self.runtime.get_runtime_settings()).FREE_DAILY_LIMIT, 9)
        self.assertEqual((await self.client.patch("/api/admin/config", headers=self.headers, json=payload)).status_code, 409)
        for values in ({"ADMIN_API_KEY": "expose"}, {"FREE_DAILY_LIMIT": -1}, {"reply_model": "unknown-model"}):
            invalid = await self.client.patch("/api/admin/config", headers=self.headers,
                                            json={"revision": saved.json()["revision"], "values": values})
            self.assertEqual(invalid.status_code, 422, invalid.text)
        from app.services.gemini import GeminiService
        service = GeminiService()
        with patch.object(service, "_generate", AsyncMock(return_value="hello")) as generate:
            self.assertEqual(await service.generate_response("system", "user"), "hello")
            self.assertEqual(generate.call_args.args[:2], ("gemini-3.5-flash-lite", "minimal"))
        audit = (await self.client.get("/api/admin/audit", headers=self.headers)).json()
        self.assertEqual(len(audit), 1)
        self.assertNotIn(admin.settings.ADMIN_API_KEY, str(audit))

    async def test_pagination_and_unknown_user(self):
        self.assertEqual((await self.client.get("/api/admin/users?limit=10000", headers=self.headers)).status_code, 422)
        self.assertEqual((await self.client.get("/api/admin/users/999", headers=self.headers)).status_code, 404)

    async def test_preview_is_not_misclassified_as_registered_active_and_expiry_is_respected(self):
        async with self.sessions() as db:
            preview = User(phone_number="910000000001", name="Preview")
            setup = User(phone_number="910000000002", name="Setup")
            expired = User(phone_number="910000000003", name="Expired", is_premium=True,
                           plan_tier="pro", premium_expires_at=datetime.utcnow() - timedelta(days=1))
            db.add_all([preview, setup, expired])
            await db.flush()
            for user in (preview, setup, expired):
                db.add(UserUsage(user_id=user.id, date=date.today(), query_count=1))
            db.add(UserOnboarding(user_id=setup.id, step="interests"))
            db.add(VerifiedWhatsAppAccount(phone_number=expired.phone_number))
            await db.commit()
        response = await self.client.get("/api/admin/users", headers=self.headers)
        states = {row["name"]: row for row in response.json()["items"]}
        self.assertEqual(states["Preview"]["stage"], "preview")
        self.assertEqual(states["Setup"]["stage"], "onboarding")
        self.assertEqual(states["Expired"]["stage"], "active")
        self.assertEqual(states["Expired"]["plan_tier"], "free")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    async def test_saved_limit_is_used_by_actual_usage_service(self):
        from app.services import usage
        config = (await self.client.get("/api/admin/config", headers=self.headers)).json()
        await self.client.patch("/api/admin/config", headers=self.headers,
                                json={"revision": config["revision"], "values": {"FREE_DAILY_LIMIT": 1}})
        async with self.sessions() as db:
            user = User(phone_number="910000000004")
            db.add(user)
            await db.flush()
            db.add(UserUsage(user_id=user.id, date=date.today(), query_count=1))
            await db.commit()
        with patch.object(usage, "async_session", self.sessions), patch.object(usage, "ensure_tables", AsyncMock()):
            status = await usage.UsageService().check_usage(user.phone_number)
        self.assertFalse(status["allowed"])
        self.assertEqual(status["limit"], 1)


if __name__ == "__main__":
    unittest.main()
