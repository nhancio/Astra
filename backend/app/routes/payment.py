"""Polar checkout, verified payment callbacks, and subscription webhooks."""

import json
import logging
from typing import Literal
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import get_settings
from app.services.auth import current_phone
from app.services.composio_service import normalize_phone
from app.services.payment import PaymentService, canonical_plan
from app.services.usage import UsageService

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/payment", tags=["payment"])
payment_service = PaymentService()
usage_service = UsageService()


class PublicPaymentLinkRequest(BaseModel):
    phone_number: str
    plan: Literal["pro", "max", "business"] = "pro"


@router.post("/create-link")
async def create_public_payment_link(req: PublicPaymentLinkRequest, owner: str = Depends(current_phone)) -> dict:
    phone = normalize_phone(req.phone_number)
    if phone != owner:
        raise HTTPException(status_code=403, detail="Payment must belong to the logged-in account")
    user = await usage_service.get_or_create_user(phone)
    tier = canonical_plan(req.plan)
    url = await payment_service.create_payment_link(f"+{phone}", user.id, plan=tier)
    if not url:
        raise HTTPException(status_code=503, detail="Polar checkout is unavailable right now")
    amount = settings.MAX_PRICE_CENTS if tier == "max" else settings.PRO_PRICE_CENTS
    return {"payment_url": url, "amount_usd": amount / 100, "currency": "USD", "plan": tier, "phone_number": phone}


@router.get("/checkout")
async def direct_checkout(plan: Literal["pro", "max", "business"] = "pro") -> RedirectResponse:
    # A public query parameter cannot bind a purchase to an account. Sign in first.
    return RedirectResponse(url=f"/app?plan={canonical_plan(plan)}", status_code=302,
                            headers={"Cache-Control": "no-store"})


@router.get("/success")
async def payment_success(request: Request) -> RedirectResponse:
    try:
        details = await payment_service.complete_callback(dict(request.query_params))
    except Exception:
        logger.exception("Polar checkout verification failed")
        raise HTTPException(status_code=503, detail="Payment verification is pending. Please try again shortly.")
    if not details:
        raise HTTPException(status_code=400, detail="A completed Astra checkout could not be verified")
    query = {"paid": "1", "plan": details["plan_tier"], "phone": details["phone_number"]}
    return RedirectResponse(url=f"/app?{urlencode(query)}", status_code=302,
                            headers={"Cache-Control": "no-store"})


@router.post("/webhook")
async def polar_webhook(request: Request) -> dict:
    body = await request.body()
    if not payment_service.verify_webhook(request.headers, body):
        raise HTTPException(status_code=401, detail="Invalid payment signature")
    try:
        payload = json.loads(body)
        event = payload.get("type", "")
        data = payload.get("data") or {}
        if data.get("product_id") and not payment_service.plan_for_product(data["product_id"]):
            return {"status": "ignored"}
        if event == "order.paid":
            subscription_id = data.get("subscription_id")
        elif event in {"subscription.active", "subscription.updated", "subscription.canceled",
                       "subscription.uncanceled", "subscription.revoked"}:
            subscription_id = data.get("id")
        else:
            return {"status": "ignored"}
        if not subscription_id:
            return {"status": "ignored"}
        applied = await payment_service.refresh_subscription(subscription_id)
        return {"status": "ok" if applied else "ignored"}
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid Polar event")
    except Exception:
        logger.exception("Polar webhook processing failed")
        # Return non-2xx so Polar retries database/API failures.
        raise HTTPException(status_code=503, detail="Payment processing is temporarily unavailable")


@router.get("/status/{phone_number}")
async def payment_status(phone_number: str, owner: str = Depends(current_phone)) -> dict:
    phone = normalize_phone(phone_number)
    if phone != owner:
        raise HTTPException(status_code=403, detail="Payment belongs to another account")
    user = await usage_service.get_or_create_user(phone)
    return {"phone_number": phone, "is_premium": user.is_premium,
            "premium_expires_at": user.premium_expires_at.isoformat() if user.premium_expires_at else None}
