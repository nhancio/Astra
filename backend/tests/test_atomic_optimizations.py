"""Regression tests for atomic SQL operations, User query fan-out, and hot-path latency."""

import asyncio
from contextlib import ExitStack
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.models.database import Base
from app.models.user import SponsoredCampaign, User, UserConnection, UserUsage
from app.routes import webhook as webhook_module
from app.services import ads_service as ads_module
from app.services import auth as auth_module
from app.services import payment as payment_module
from app.services import usage as usage_module
from app.services.ads_service import AdsService
from app.services.composio_service import ComposioService
from app.services.gemini import GeminiService
from app.services.memory import memory_service
from app.services.payment import PaymentService
from app.services.usage import UsageService
from app.services.whatsapp import WhatsAppService

PHONE = "919876543210"


class AtomicAndLatencyOptimizationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for mod in (usage_module, ads_module, auth_module):
            self.stack.enter_context(patch.object(mod, "async_session", self.sessions))
            self.stack.enter_context(patch.object(mod, "ensure_tables", AsyncMock()))

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_user_fetch_does_not_trigger_selectin_fanout_queries(self):
        svc = UsageService()
        await svc.get_or_create_user(PHONE)

        statements: list[str] = []

        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        event.listen(self.engine.sync_engine, "before_cursor_execute", before_cursor_execute)
        try:
            await svc.get_or_create_user(PHONE)
        finally:
            event.remove(self.engine.sync_engine, "before_cursor_execute", before_cursor_execute)

        self.assertEqual(
            len(statements),
            1,
            f"Expected 1 SELECT for User, got {len(statements)}: {statements}",
        )

    async def test_concurrent_increment_usage_is_atomic_without_lost_updates(self):
        svc = UsageService()
        await svc.get_or_create_user(PHONE)

        await asyncio.gather(*(svc.increment_usage(PHONE) for _ in range(5)))

        async with self.sessions() as session:
            row = await session.scalar(select(UserUsage))
            self.assertIsNotNone(row)
            self.assertEqual(row.query_count, 5)

    async def test_ad_impression_and_click_use_sql_atomic_increments_and_budget_cap(self):
        ads = AdsService()
        async with self.sessions() as session:
            camp = SponsoredCampaign(
                brand_name="Atomic Brand",
                category="travel",
                target_intent="travel_irctc",
                headline="Test headline",
                cta_text="Book",
                cta_url="https://example.test/ad",
                cpm_inr=300,  # 30 paise per impression
                budget_paise=60,  # Exactly 2 impressions budget
                spent_paise=0,
                impressions=0,
                clicks=0,
                is_active=True,
            )
            session.add(camp)
            await session.commit()
            camp_id = camp.id

        # Simulate stale in-memory state by running two impressions and clicks
        with patch.object(ads_module.settings, "ADS_ENABLED", True):
            ad1 = await ads.get_contextual_ad("travel_irctc")
            ad2 = await ads.get_contextual_ad("travel_irctc")
            ad3 = await ads.get_contextual_ad("travel_irctc")
        self.assertIsNotNone(ad1)
        self.assertIsNotNone(ad2)
        self.assertIsNone(ad3, "Campaign should auto-pause once spent_paise >= budget_paise")

        await asyncio.gather(*(ads.record_click(camp_id) for _ in range(4)))

        async with self.sessions() as session:
            updated = await session.get(SponsoredCampaign, camp_id)
            self.assertEqual(updated.impressions, 2)
            self.assertEqual(updated.spent_paise, 60)
            self.assertFalse(updated.is_active)
            self.assertEqual(updated.clicks, 4)

    async def test_ad_seeding_retires_legacy_campaigns_without_losing_stats_or_duplicates(self):
        async with self.sessions() as session:
            legacy = SponsoredCampaign(
                brand_name="Zepto Pass", category="shopping", target_intent="all",
                headline="Old offer", cta_text="Shop",
                cta_url="https://www.zeptonow.com/?utm_source=astra_ai_whatsapp",
                impressions=12, clicks=3, spent_paise=312, is_active=True,
            )
            custom = SponsoredCampaign(
                brand_name="Custom Brand", category="general", target_intent="all",
                headline="Custom offer", cta_text="Visit", cta_url="https://example.test/ad",
                is_active=True,
            )
            session.add_all([legacy, custom])
            await session.commit()
            legacy_id, custom_id = legacy.id, custom.id

        ads = AdsService()
        await ads.ensure_seeded()
        await ads.ensure_seeded()

        async with self.sessions() as session:
            rows = list((await session.scalars(select(SponsoredCampaign))).all())
            self.assertEqual(len(rows), 8)
            retired = await session.get(SponsoredCampaign, legacy_id)
            self.assertFalse(retired.is_active)
            self.assertEqual((retired.impressions, retired.clicks, retired.spent_paise), (12, 3, 312))
            self.assertTrue((await session.get(SponsoredCampaign, custom_id)).is_active)
            replacements = [row for row in rows if row.id not in {legacy_id, custom_id}]
            self.assertEqual({row.cta_url for row in replacements}, {
                "https://tryengage.si", "https://tryastra.web.app", "https://nhancio.com",
                "https://magicboxai.in", "https://heyceo.lol", "https://tweleb.web.app",
            })
            self.assertTrue(all(row.is_active and row.target_intent == "all" for row in replacements))
            paused_id = replacements[0].id
            replacements[0].is_active = False
            await session.commit()

        await ads.ensure_seeded()
        async with self.sessions() as session:
            self.assertFalse((await session.get(SponsoredCampaign, paused_id)).is_active)

    async def test_get_user_connections_skips_remote_http_when_user_has_no_stored_connections(self):
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"items": [], "next_cursor": None})

        config = Settings(_env_file=None, COMPOSIO_API_KEY="test-key")
        composio = ComposioService(
            config=config,
            session_factory=self.sessions,
            initialize=AsyncMock(),
            transport=httpx.MockTransport(respond),
        )
        conns = await composio.get_user_connections(PHONE)
        self.assertTrue(all(c["status"] == "disconnected" for c in conns))
        self.assertEqual(
            requests,
            [],
            "Users with no stored UserConnection rows must not pay a live Composio HTTP roundtrip on every message",
        )

    async def test_concurrent_upsert_connection_is_atomic(self):
        config = Settings(_env_file=None, COMPOSIO_API_KEY="test-key")
        composio = ComposioService(
            config=config,
            session_factory=self.sessions,
            initialize=AsyncMock(),
        )
        await asyncio.gather(
            *(
                composio._upsert_connection(PHONE, "gmail", "active", connection_id=f"ca_{i}")
                for i in range(4)
            )
        )
        async with self.sessions() as session:
            rows = (
                await session.execute(
                    select(UserConnection).where(
                        UserConnection.phone_number == PHONE,
                        UserConnection.toolkit == "gmail",
                    )
                )
            ).scalars().all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].status, "active")

    async def test_polar_uses_a_reusable_async_http_client(self):
        svc = PaymentService()
        self.assertIs(svc._get_client(), svc._get_client())
        await svc.close()

    async def test_webhook_dedup_uses_shared_atomic_claim_once_and_login_challenge_cannot_be_overwritten(self):
        with patch.object(webhook_module, "PROCESSED_MESSAGE_IDS", {}), \
             patch.object(memory_service, "_get_redis", AsyncMock(return_value=None)):
            # First worker records message in the shared database; a second worker with a cold cache still deduplicates
            first = await webhook_module.check_and_record_message("wamid.cross-worker-1")
            webhook_module.PROCESSED_MESSAGE_IDS.clear()
            second = await webhook_module.check_and_record_message("wamid.cross-worker-1")
            self.assertFalse(first)
            self.assertTrue(second, "Second worker must deduplicate via shared claim_once even with cold local dict")

            # Login challenge cannot be overwritten by a second phone once claimed
            ch = await auth_module.start_whatsapp_login_challenge()
            code = ch["code"]
            ok1, _ = await auth_module.complete_whatsapp_login_from_webhook(PHONE, code=code)
            ok2, _ = await auth_module.complete_whatsapp_login_from_webhook("919999999999", code=code)
            self.assertTrue(ok1)
            self.assertFalse(ok2, "Already-claimed login code must reject overwrite from another sender")

    def test_http_services_reuse_persistent_async_client(self):
        gemini = GeminiService()
        wa = WhatsAppService()
        self.assertIs(gemini._get_client(), gemini._get_client())
        self.assertIs(wa._get_client(), wa._get_client())
