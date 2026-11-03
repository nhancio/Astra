"""Read shared overrides on each operation so every Cloud Run instance agrees."""
from types import SimpleNamespace
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.models.admin import RuntimeConfig
from app.models.database import async_session, ensure_tables

ModelName = Literal["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]


class RuntimeValues(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reply_model: ModelName = "gemini-3.8-flash"
    fast_model: ModelName = "gemini-3.5-flash-lite"
    json_model: ModelName = "gemini-3.1-flash-lite"
    FREE_DAILY_LIMIT: int = Field(5, ge=0, le=10000)
    PAID_DAILY_LIMIT: int = Field(10, ge=0, le=10000)
    MAX_DAILY_LIMIT: int = Field(30, ge=0, le=10000)
    SIGNUP_PREVIEW_MESSAGES: int = Field(2, ge=0, le=100)
    ADS_ENABLED: bool = True


def defaults() -> dict:
    env = get_settings().model_dump()
    values = RuntimeValues().model_dump()
    values = {key: env.get(key, value) for key, value in values.items()}
    if "MAX_DAILY_LIMIT" not in env:
        values["MAX_DAILY_LIMIT"] = env.get("BUSINESS_DAILY_LIMIT", 30)
    return values


async def read_config() -> dict:
    await ensure_tables()
    async with async_session() as db:
        row = await db.get(RuntimeConfig, 1)
        # Create the singleton once; concurrent first requests can safely race.
        if row is None:
            db.add(RuntimeConfig(id=1, revision=1, values={}))
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
            row = await db.get(RuntimeConfig, 1)
        return {"revision": row.revision, "values": defaults() | row.values,
                "updated_at": row.updated_at}


async def get_runtime_settings() -> SimpleNamespace:
    config = await read_config()
    values = get_settings().model_dump() | config["values"]
    # Keep the live Business tier and the incoming Max tier on the same operational cap.
    values["BUSINESS_DAILY_LIMIT"] = values["MAX_DAILY_LIMIT"]
    return SimpleNamespace(**values)
