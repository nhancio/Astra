"""Polar hosted checkout and verified monthly subscription entitlements."""

import base64
import binascii
from datetime import datetime, timezone
import hashlib
import hmac
import logging
import time
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select

from app.config import get_settings
from app.models.database import async_session, ensure_tables
from app.models.user import PolarSubscription, User
from app.services.composio_service import normalize_phone
from app.services.usage import UsageService

logger = logging.getLogger(__name__)
settings = get_settings()
PRODUCT_TAG = "astra"


def canonical_plan(plan: str) -> str:
    return "max" if plan in ("max", "business") else "pro"


def utc_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)


class PaymentService:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=20)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        if not settings.POLAR_ACCESS_TOKEN:
            raise RuntimeError("Polar access token is not configured")
        host = "sandbox-api.polar.sh" if settings.POLAR_SERVER == "sandbox" else "api.polar.sh"
        response = await self._get_client().request(
            method, f"https://{host}/v1/{path}",
            headers={"Authorization": f"Bearer {settings.POLAR_ACCESS_TOKEN}", "Polar-Version": "2026-10"},
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def plan_for_product(self, product_id: str) -> str | None:
        if product_id and product_id == settings.POLAR_PRO_PRODUCT_ID:
            return "pro"
        if product_id and product_id == settings.POLAR_MAX_PRODUCT_ID:
            return "max"
        return None

    async def create_payment_link(self, phone_number: str = "", user_id: int | None = None, plan: str = "pro") -> str | None:
        """Only trusted callers supply the account phone; Polar collects billing email."""
        phone = normalize_phone(phone_number) if phone_number else ""
        tier = canonical_plan(plan)
        product_id = settings.POLAR_MAX_PRODUCT_ID if tier == "max" else settings.POLAR_PRO_PRODUCT_ID
        if not phone or not product_id or not settings.POLAR_ACCESS_TOKEN:
            return None
        metadata: dict[str, Any] = {"product": PRODUCT_TAG, "plan_tier": tier, "phone_number": phone}
        if user_id is not None:
            metadata["user_id"] = str(user_id)
        try:
            checkout = await self._request("POST", "checkouts/", json={
                "products": [product_id],
                "external_customer_id": f"astra:{phone}",
                "metadata": metadata,
                "allow_trial": False,
                "allow_discount_codes": False,
                "success_url": f"{settings.APP_URL.rstrip('/')}/payment/success?checkout_id={{CHECKOUT_ID}}",
                "return_url": f"{settings.APP_FRONTEND_URL.rstrip('/')}/app",
            })
            return checkout.get("url")
        except (httpx.HTTPError, RuntimeError):
            # Do not log provider response bodies or URLs containing checkout secrets.
            logger.exception("Polar checkout creation failed")
            return None

    def verify_webhook(self, headers: Any, body: bytes) -> bool:
        """Validate Standard Webhooks signatures, including legacy Polar HMAC keys."""
        secret = settings.POLAR_WEBHOOK_SECRET
        event_id = headers.get("webhook-id", "")
        stamp = headers.get("webhook-timestamp", "")
        signature = headers.get("webhook-signature", "")
        if not secret or not event_id or not signature:
            return False
        try:
            if abs(time.time() - int(stamp)) > 300:
                return False
            keys = [secret.encode()]
            encoded = secret.removeprefix("whsec_")
            try:
                keys.append(base64.b64decode(encoded, validate=True))
            except (ValueError, binascii.Error):
                pass
            message = event_id.encode() + b"." + stamp.encode() + b"." + body
            signatures = [part[3:] for part in signature.split() if part.startswith("v1,")]
            return any(hmac.compare_digest(base64.b64encode(hmac.new(key, message, hashlib.sha256).digest()).decode(), candidate)
                       for key in keys for candidate in signatures)
        except (ValueError, TypeError):
            return False

    async def refresh_subscription(self, subscription_id: str) -> bool:
        # Fetch current state so a delayed paid event cannot revive a revoked subscription.
        UUID(subscription_id)
        subscription = await self._request("GET", f"subscriptions/{subscription_id}")
        return await self.sync_subscription(subscription)

    async def sync_subscription(self, subscription: dict[str, Any]) -> bool:
        tier = self.plan_for_product(subscription.get("product_id", ""))
        metadata = subscription.get("metadata") or {}
        phone = normalize_phone(str(metadata.get("phone_number") or ""))
        if not tier or metadata.get("product") != PRODUCT_TAG or not phone:
            return False
        expires = utc_datetime(subscription["current_period_end"])
        modified = utc_datetime(subscription.get("modified_at") or subscription["created_at"])
        now = datetime.utcnow()
        active = subscription["status"] == "active" and expires > now
        await ensure_tables()
        async with async_session() as session:
            user = await UsageService().get_or_create_user(phone, session=session)
            # Serialize subscription updates for this user, including concurrent renewals.
            user = await session.scalar(select(User).where(User.id == user.id).with_for_update())
            stored = await session.get(PolarSubscription, subscription["id"])
            if stored is not None and stored.modified_at > modified:
                return True
            await session.merge(PolarSubscription(
                id=subscription["id"], user_id=user.id, plan_tier=tier,
                expires_at=expires, is_active=active, modified_at=modified,
            ))
            await session.flush()
            subscriptions = (await session.scalars(select(PolarSubscription).where(
                PolarSubscription.user_id == user.id, PolarSubscription.is_active.is_(True),
                PolarSubscription.expires_at > now,
            ))).all()
            best = max(subscriptions, key=lambda sub: (sub.plan_tier == "max", sub.expires_at), default=None)
            user.is_premium = best is not None
            user.plan_tier = best.plan_tier if best else "free"
            user.premium_expires_at = best.expires_at if best else None
            await session.commit()
        return True

    async def complete_callback(self, params: dict[str, str]) -> dict[str, str] | None:
        checkout_id = params.get("checkout_id", "")
        try:
            UUID(checkout_id)
        except ValueError:
            return None
        checkout = await self._request("GET", f"checkouts/{checkout_id}")
        metadata = checkout.get("metadata") or {}
        tier = self.plan_for_product(checkout.get("product_id", ""))
        if checkout.get("status") != "succeeded" or metadata.get("product") != PRODUCT_TAG or not tier:
            return None
        phone = normalize_phone(str(metadata.get("phone_number") or ""))
        subscription_id = checkout.get("subscription_id")
        if not phone or not subscription_id or not await self.refresh_subscription(subscription_id):
            return None
        return {"phone_number": phone, "plan_tier": tier}
