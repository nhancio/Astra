"""Sponsored message ads for free-tier WhatsApp users."""

import logging
import random
from typing import Any, Optional

from sqlalchemy import and_, case, select, update

from app.config import get_settings
from app.services.runtime import get_runtime_settings
from app.models.database import async_session, ensure_tables
from app.models.user import SponsoredCampaign

logger = logging.getLogger(__name__)
settings = get_settings()

DEFAULT_INDIA_CAMPAIGNS: list[dict[str, Any]] = [
    {
        "brand_name": "tryengage.si",
        "category": "career",
        "target_intent": "all",
        "headline": "Get hired in minutes.",
        "cta_text": "Get hired",
        "cta_url": "https://tryengage.si",
        "cpm_inr": 320,
        "budget_paise": 500000,  # ₹5,000 seeded wallet
        "spent_paise": 0,
        "is_active": True,
    },
    {
        "brand_name": "tryastra.web.app",
        "category": "general",
        "target_intent": "all",
        "headline": "Go premium for unlimited messages.",
        "cta_text": "Go premium",
        "cta_url": "https://tryastra.web.app",
        "cpm_inr": 280,
        "budget_paise": 500000,
        "spent_paise": 0,
        "is_active": True,
    },
    {
        "brand_name": "nhancio.com",
        "category": "general",
        "target_intent": "all",
        "headline": "Build your next project with an AI-native agency.",
        "cta_text": "Build your project",
        "cta_url": "https://nhancio.com",
        "cpm_inr": 450,
        "budget_paise": 500000,
        "spent_paise": 0,
        "is_active": True,
    },
    {
        "brand_name": "magicboxai.in",
        "category": "general",
        "target_intent": "all",
        "headline": "Your UGC marketing factory.",
        "cta_text": "Create UGC",
        "cta_url": "https://magicboxai.in",
        "cpm_inr": 380,
        "budget_paise": 500000,
        "spent_paise": 0,
        "is_active": True,
    },
    {
        "brand_name": "heyceo.lol",
        "category": "general",
        "target_intent": "all",
        "headline": "Join a community of CEOs.",
        "cta_text": "Join the community",
        "cta_url": "https://heyceo.lol",
        "cpm_inr": 260,
        "budget_paise": 500000,
        "spent_paise": 0,
        "is_active": True,
    },
    {
        "brand_name": "tweleb.web.app",
        "category": "general",
        "target_intent": "all",
        "headline": "Monetise your Twitter audience, faster.",
        "cta_text": "Monetise your audience",
        "cta_url": "https://tweleb.web.app",
        "cpm_inr": 300,
        "budget_paise": 500000,
        "spent_paise": 0,
        "is_active": True,
    },
]

LEGACY_CAMPAIGN_URLS = {
    "https://www.makemytrip.com/?utm_source=astra_ai_whatsapp",
    "https://www.swiggy.com/?utm_source=astra_ai_whatsapp",
    "https://cred.club/?utm_source=astra_ai_whatsapp",
    "https://www.instahyre.com/?utm_source=astra_ai_whatsapp",
    "https://www.zeptonow.com/?utm_source=astra_ai_whatsapp",
}

INTENT_TO_CATEGORY: dict[str, str] = {
    "travel_irctc": "travel",
    "railway/flight": "travel",
    "food_commerce": "food",
    "food_order": "food",
    "budget_planning": "finance",
    "tax/upi": "finance",
    "job_search": "career",
    "resume_help": "career",
    "founder_outreach": "career",
    "founder_pitch": "career",
    "task_planning": "shopping",
    "email_draft": "career",
}


class AdsService:
    """Manages sponsored campaigns, contextual matching, impression debits, and click tracking."""

    async def ensure_seeded(self) -> None:
        """Seed message ads and retire legacy defaults, retaining their statistics."""
        try:
            await ensure_tables()
            async with async_session() as session:
                result = await session.execute(select(SponsoredCampaign))
                campaigns = list(result.scalars().all())
                legacy = [camp for camp in campaigns if camp.cta_url in LEGACY_CAMPAIGN_URLS]
                if campaigns and not legacy:
                    return
                for camp in legacy:
                    camp.is_active = False
                existing_urls = {camp.cta_url for camp in campaigns}
                for item in DEFAULT_INDIA_CAMPAIGNS:
                    if item["cta_url"] not in existing_urls:
                        session.add(SponsoredCampaign(**item))
                await session.commit()
        except Exception as exc:
            logger.debug("Ad seed skipped: %s", exc)

    async def get_contextual_ad(
        self, intent: str, is_premium: bool = False, is_crisis: bool = False
    ) -> Optional[str]:
        """Select an ad, debit the campaign wallet, and return the formatted WhatsApp card."""
        settings = await get_runtime_settings()
        if not settings.ADS_ENABLED or is_premium or is_crisis or intent == "just_venting":
            return None

        await self.ensure_seeded()
        category = INTENT_TO_CATEGORY.get(intent, "")

        try:
            async with async_session() as session:
                # Query active campaigns
                stmt = select(SponsoredCampaign).where(SponsoredCampaign.is_active.is_(True))
                
                # Match by target_intent or category
                matched: list[SponsoredCampaign] = []
                if intent:
                    intent_res = await session.execute(
                        stmt.where(
                            (SponsoredCampaign.target_intent == intent) |
                            (SponsoredCampaign.target_intent == "all") |
                            (SponsoredCampaign.category == category)
                        )
                    )
                    matched = list(intent_res.scalars().all())

                if not matched:
                    all_res = await session.execute(stmt)
                    matched = list(all_res.scalars().all())

                if not matched:
                    return None

                chosen = random.choice(matched)

                # Calculate impression cost in paise: (cpm_inr * 100) / 1000 = cpm_inr / 10
                cost_paise = max(1, int((chosen.cpm_inr * 100) / 1000))
                new_spent = SponsoredCampaign.spent_paise + cost_paise

                # Atomic impression & wallet debit; auto-pause when prepaid wallet hits budget
                debited = await session.execute(
                    update(SponsoredCampaign)
                    .where(
                        SponsoredCampaign.id == chosen.id,
                        SponsoredCampaign.is_active.is_(True),
                        (SponsoredCampaign.budget_paise <= 0)
                        | (SponsoredCampaign.spent_paise < SponsoredCampaign.budget_paise),
                    )
                    .values(
                        impressions=SponsoredCampaign.impressions + 1,
                        spent_paise=new_spent,
                        is_active=case(
                            (
                                and_(
                                    SponsoredCampaign.budget_paise > 0,
                                    new_spent >= SponsoredCampaign.budget_paise,
                                ),
                                False,
                            ),
                            else_=SponsoredCampaign.is_active,
                        ),
                    )
                )
                await session.commit()
                if debited.rowcount == 0:
                    return None

                # Generate custom tracking click redirect URL
                track_url = f"{settings.APP_URL}/r/{chosen.id}"

                return (
                    f"━━━━━━━━━━━━━━━\n"
                    f"⚡ *Sponsored • {chosen.brand_name}*\n"
                    f"{chosen.headline}\n"
                    f"👉 _{chosen.cta_text}:_ {track_url}"
                )
        except Exception as exc:
            logger.debug("Ad selection failed: %s", exc)
            return None

    async def record_click(self, campaign_id: int) -> Optional[str]:
        """Atomically record click and return destination URL for redirect."""
        try:
            await ensure_tables()
            async with async_session() as session:
                cta_url = await session.scalar(
                    select(SponsoredCampaign.cta_url).where(SponsoredCampaign.id == campaign_id)
                )
                if not cta_url:
                    return None

                await session.execute(
                    update(SponsoredCampaign)
                    .where(SponsoredCampaign.id == campaign_id)
                    .values(clicks=SponsoredCampaign.clicks + 1)
                )
                await session.commit()
                return cta_url
        except Exception as exc:
            logger.error("Click record error: %s", exc)
            return None

    async def list_campaigns(self) -> list[dict[str, Any]]:
        """List all campaigns with live stats and wallet metrics."""
        await self.ensure_seeded()
        async with async_session() as session:
            result = await session.execute(
                select(SponsoredCampaign).order_by(SponsoredCampaign.id.desc())
            )
            rows = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "brand_name": r.brand_name,
                    "category": r.category,
                    "target_intent": getattr(r, "target_intent", "all"),
                    "headline": r.headline,
                    "cta_text": r.cta_text,
                    "cta_url": r.cta_url,
                    "cpm_inr": r.cpm_inr,
                    "budget_paise": getattr(r, "budget_paise", 0),
                    "budget_inr": getattr(r, "budget_paise", 0) / 100,
                    "spent_paise": getattr(r, "spent_paise", 0),
                    "spent_inr": getattr(r, "spent_paise", 0) / 100,
                    "remaining_inr": max(0, (getattr(r, "budget_paise", 0) - getattr(r, "spent_paise", 0)) / 100),
                    "impressions": r.impressions,
                    "clicks": r.clicks,
                    "ctr_percent": round((r.clicks / r.impressions * 100), 2) if r.impressions > 0 else 0.0,
                    "is_active": r.is_active,
                    "contact_email": getattr(r, "contact_email", None),
                    "contact_phone": getattr(r, "contact_phone", None),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

    async def create_campaign(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new brand sponsored campaign."""
        await ensure_tables()
        budget_inr = int(data.get("budget_inr", 5000))
        budget_paise = budget_inr * 100
        cpm_inr = int(data.get("cpm_inr", 300))

        async with async_session() as session:
            camp = SponsoredCampaign(
                brand_name=data["brand_name"],
                category=data.get("category", "general"),
                target_intent=data.get("target_intent", "all"),
                headline=data["headline"],
                cta_text=data["cta_text"],
                cta_url=data["cta_url"],
                cpm_inr=cpm_inr,
                budget_paise=budget_paise,
                spent_paise=0,
                is_active=data.get("is_active", True),
                contact_email=data.get("contact_email"),
                contact_phone=data.get("contact_phone"),
            )
            session.add(camp)
            await session.commit()
            await session.refresh(camp)
            return {
                "id": camp.id,
                "brand_name": camp.brand_name,
                "category": camp.category,
                "target_intent": camp.target_intent,
                "budget_inr": budget_inr,
                "cpm_inr": cpm_inr,
                "is_active": camp.is_active,
            }

    async def toggle_campaign(self, campaign_id: int) -> bool:
        """Toggle a campaign active/paused."""
        async with async_session() as session:
            res = await session.execute(
                select(SponsoredCampaign).where(SponsoredCampaign.id == campaign_id)
            )
            camp = res.scalar_one_or_none()
            if not camp:
                return False
            camp.is_active = not camp.is_active
            await session.commit()
            return camp.is_active
