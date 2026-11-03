"""Checkout ownership, Polar signature validation, and replay-safe entitlements."""

import base64
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import time
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.database import Base
from app.models.user import PolarSubscription, User
from app.routes import payment as routes
from app.services import payment
from app.services.usage import UsageService

PHONE = "919876543210"
SECRET = "whsec_" + base64.b64encode(b"astra-test-secret").decode()
CHECKOUT_ID = "7b8bae0f-fa9f-491f-ba1a-58cd384cec63"
SUBSCRIPTION_ID = "1b8bae0f-fa9f-491f-ba1a-58cd384cec63"


def signed_headers(body, timestamp=None):
    stamp = str(timestamp if timestamp is not None else int(time.time()))
    message = b"event_1." + stamp.encode() + b"." + body
    signature = base64.b64encode(hmac.new(base64.b64decode(SECRET[6:]), message, hashlib.sha256).digest()).decode()
    return {"webhook-id": "event_1", "webhook-timestamp": stamp, "webhook-signature": "v1," + signature}


class PolarTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for key, value in {"POLAR_ACCESS_TOKEN": "test", "POLAR_WEBHOOK_SECRET": SECRET,
                           "POLAR_PRO_PRODUCT_ID": "prod_pro", "POLAR_MAX_PRODUCT_ID": "prod_max"}.items():
            self.stack.enter_context(patch.object(payment.settings, key, value))
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.stack.enter_context(patch.object(payment, "async_session", self.sessions))
        self.stack.enter_context(patch.object(payment, "ensure_tables", AsyncMock()))
        self.svc = payment.PaymentService()
        app = FastAPI()
        app.include_router(routes.router)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.engine.dispose()

    def subscription(self, tier="max", status="active", sub_id="sub_1"):
        return {"id": sub_id, "status": status, "product_id": "prod_" + tier,
                "current_period_end": (datetime.now(timezone.utc) + timedelta(days=28)).isoformat(),
                "modified_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {"product": "astra", "phone_number": PHONE, "plan_tier": tier}}

    async def test_checkout_uses_configured_product_and_verified_identity(self):
        requests = []
        def respond(req):
            requests.append(req)
            return httpx.Response(201, json={"url": "https://checkout.polar.sh/test"})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            with patch.object(self.svc, "_get_client", return_value=client):
                self.assertEqual(await self.svc.create_payment_link("+" + PHONE, 123, "business"), "https://checkout.polar.sh/test")
        payload = json.loads(requests[0].content)
        self.assertEqual(payload["products"], ["prod_max"])
        self.assertEqual(payload["metadata"]["phone_number"], PHONE)
        self.assertEqual(payload["external_customer_id"], "astra:" + PHONE)
        self.assertFalse(payload["allow_trial"])
        self.assertIn("checkout_id={CHECKOUT_ID}", payload["success_url"])
        self.assertIsNone(await self.svc.create_payment_link("", None, "pro"))

    async def test_duplicate_events_keep_exact_expiry_and_ignore_other_products(self):
        sub = self.subscription()
        for _ in range(2):
            self.assertTrue(await self.svc.sync_subscription(sub))
        async with self.sessions() as db:
            users = (await db.scalars(select(User))).all()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].plan_tier, "max")
            self.assertEqual(users[0].premium_expires_at, datetime.fromisoformat(sub["current_period_end"]).replace(tzinfo=None))
        sub["product_id"] = "another_app"
        self.assertFalse(await self.svc.sync_subscription(sub))

    async def test_revocation_preserves_another_paid_subscription(self):
        await self.svc.sync_subscription(self.subscription("pro", sub_id="sub_pro"))
        await self.svc.sync_subscription(self.subscription())
        await self.svc.sync_subscription(self.subscription(status="canceled"))
        async with self.sessions() as db:
            user = await db.scalar(select(User))
            self.assertTrue(user.is_premium)
            self.assertEqual(user.plan_tier, "pro")
        await self.svc.sync_subscription(self.subscription("pro", "canceled", "sub_pro"))
        async with self.sessions() as db:
            self.assertFalse((await db.scalar(select(User))).is_premium)

    async def test_invalid_stale_and_unsigned_webhooks_are_rejected(self):
        body = b'{"type":"order.paid","data":{"subscription_id":"sub_1"}}'
        with patch.object(routes.payment_service, "refresh_subscription", AsyncMock()) as refresh:
            for headers in ({}, signed_headers(body, int(time.time()) - 601), signed_headers(body + b" ")):
                response = await self.client.post("/payment/webhook", content=body, headers=headers)
                self.assertEqual(response.status_code, 401)
            refresh.assert_not_awaited()

    async def test_paid_and_revoked_events_refresh_authoritative_subscription(self):
        for event, data in [("order.paid", {"subscription_id": "sub_1"}), ("subscription.revoked", {"id": "sub_1"})]:
            body = json.dumps({"type": event, "data": data}).encode()
            with patch.object(routes.payment_service, "refresh_subscription", AsyncMock(return_value=True)) as refresh:
                response = await self.client.post("/payment/webhook", content=body, headers=signed_headers(body))
            self.assertEqual(response.status_code, 200)
            refresh.assert_awaited_once_with("sub_1")

    async def test_processing_failure_is_retryable(self):
        body = b'{"type":"subscription.updated","data":{"id":"sub_1"}}'
        with patch.object(routes.payment_service, "refresh_subscription", AsyncMock(side_effect=RuntimeError("db"))):
            response = await self.client.post("/payment/webhook", content=body, headers=signed_headers(body))
        self.assertEqual(response.status_code, 503)

    async def test_guest_checkout_requires_sign_in_and_keeps_legacy_plan_choice(self):
        response = await self.client.get("/payment/checkout?plan=business&phone=919999999999")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["location"], "/app?plan=max")

    async def test_unpaid_callback_cannot_claim_success_or_query_identity(self):
        for checkout in ({"status": "open", "product_id": "prod_max", "metadata": {"product": "astra"}},
                         {"status": "succeeded", "product_id": "prod_max", "metadata": {"product": "another_app"}}):
            with patch.object(self.svc, "_request", AsyncMock(return_value=checkout)) as fetch:
                self.assertIsNone(await self.svc.complete_callback({"checkout_id": CHECKOUT_ID, "phone": PHONE, "plan": "max"}))
                fetch.assert_awaited_once()
        with patch.object(routes.payment_service, "complete_callback", AsyncMock(return_value=None)):
            response = await self.client.get("/payment/success?checkout_id=unpaid")
        self.assertEqual(response.status_code, 400)

    async def test_successful_callback_uses_only_polar_identity_and_plan(self):
        checkout = {"status": "succeeded", "product_id": "prod_pro", "subscription_id": SUBSCRIPTION_ID,
                    "metadata": {"product": "astra", "phone_number": PHONE}}
        with patch.object(self.svc, "_request", AsyncMock(return_value=checkout)), \
             patch.object(self.svc, "refresh_subscription", AsyncMock(return_value=True)) as refresh:
            details = await self.svc.complete_callback({"checkout_id": CHECKOUT_ID, "phone": "919999999999", "plan": "max"})
        self.assertEqual(details, {"phone_number": PHONE, "plan_tier": "pro"})
        refresh.assert_awaited_once_with(SUBSCRIPTION_ID)
        with patch.object(routes.payment_service, "complete_callback", AsyncMock(return_value=details)):
            response = await self.client.get("/payment/success?checkout_id=" + CHECKOUT_ID)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/app?paid=1&plan=pro&phone=" + PHONE, response.headers["location"])

    async def test_expired_max_falls_back_to_remaining_pro_subscription(self):
        await self.svc.sync_subscription(self.subscription("pro", sub_id="sub_pro"))
        await self.svc.sync_subscription(self.subscription())
        async with self.sessions() as db:
            (await db.scalar(select(User))).premium_expires_at = datetime.utcnow() - timedelta(days=1)
            (await db.get(PolarSubscription, "sub_1")).expires_at = datetime.utcnow() - timedelta(days=1)
            await db.commit()
        async with self.sessions() as db:
            user = await UsageService().get_or_create_user(PHONE, session=db)
            self.assertTrue(user.is_premium)
            self.assertEqual(user.plan_tier, "pro")

    async def test_stale_subscription_state_cannot_overwrite_a_later_revocation(self):
        stale = self.subscription()
        await self.svc.sync_subscription(stale)
        await self.svc.sync_subscription(self.subscription(status="canceled"))
        await self.svc.sync_subscription(stale)
        async with self.sessions() as db:
            self.assertFalse((await db.scalar(select(User))).is_premium)

    async def test_shared_account_event_for_another_product_is_ignored(self):
        body = b'{"type":"order.paid","data":{"subscription_id":"sub_1","product_id":"another_app"}}'
        with patch.object(routes.payment_service, "refresh_subscription", AsyncMock()) as refresh:
            response = await self.client.post("/payment/webhook", content=body, headers=signed_headers(body))
        self.assertEqual(response.json(), {"status": "ignored"})
        refresh.assert_not_awaited()
