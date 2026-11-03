"""Record classifications without retaining message contents."""
import asyncio
import logging
from app.models.admin import ActivityEvent
from app.models.database import async_session


async def record_activity(phone: str, intent: str, emotion: str | None) -> None:
    try:
        async with asyncio.timeout(0.5):
            async with async_session() as db:
                db.add(ActivityEvent(phone_number=phone, intent=intent, emotion=emotion))
                await db.commit()
    except Exception:
        logging.getLogger(__name__).warning("Activity telemetry write unavailable")
