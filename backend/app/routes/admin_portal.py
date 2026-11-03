"""Protected operational views; only measured data is returned."""
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import case, func, or_, select, update

from app.config import get_settings
from app.models.admin import ActivityEvent, AdminAudit, ModelCall, RuntimeConfig
from app.models.database import async_session
from app.models.onboarding import UserOnboarding
from app.models.tool_run import ToolRun
from app.models.user import FlowLog, User, UserConnection, UserUsage, VerifiedWhatsAppAccount
from app.routes.admin import verify_admin_key
from app.services.runtime import MODELS, RuntimeValues, read_config


async def private_response(response: Response):
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(prefix="/api/admin", tags=["admin portal"],
                   dependencies=[Depends(verify_admin_key), Depends(private_response)])
Stage = Literal["preview", "onboarding", "ready", "active", "dormant", "paid"]


def user_view():
    usage = select(UserUsage.user_id, func.sum(UserUsage.query_count).label("total_queries"),
                   func.max(case((UserUsage.query_count > 0, UserUsage.date))).label("last_active"),
                   func.sum(case((UserUsage.date == date.today(), UserUsage.query_count), else_=0)).label("used_today"),
                   ).group_by(UserUsage.user_id).subquery()
    connections = select(UserConnection.phone_number, func.count().label("connected_apps")).where(
        UserConnection.status == "active").group_by(UserConnection.phone_number).subquery()
    paid = User.is_premium.is_(True) & or_(User.premium_expires_at.is_(None), User.premium_expires_at > datetime.utcnow())
    registered = or_(UserOnboarding.user_id.is_not(None), VerifiedWhatsAppAccount.phone_number.is_not(None))
    stage = case((paid, "paid"),
                 (~registered, "preview"),
                 (UserOnboarding.user_id.is_not(None) & UserOnboarding.completed_at.is_(None), "onboarding"),
                 (usage.c.last_active >= date.today() - timedelta(days=6), "active"),
                 (usage.c.last_active.is_not(None), "dormant"),
                 (UserOnboarding.completed_at.is_not(None), "ready"),
                 (registered, "onboarding"),
                 else_="preview")
    return select(User.id, User.name, User.phone_number, User.city, User.preferred_language,
                  User.created_at, User.premium_expires_at,
                  case((paid, User.plan_tier), else_="free").label("plan_tier"),
                  UserOnboarding.step.label("setup_step"), stage.label("stage"),
                  func.coalesce(usage.c.total_queries, 0).label("total_queries"),
                  func.coalesce(usage.c.used_today, 0).label("used_today"), usage.c.last_active,
                  func.coalesce(connections.c.connected_apps, 0).label("connected_apps")).outerjoin(
        usage, usage.c.user_id == User.id).outerjoin(UserOnboarding, UserOnboarding.user_id == User.id).outerjoin(
        connections, connections.c.phone_number == User.phone_number).outerjoin(
        VerifiedWhatsAppAccount, VerifiedWhatsAppAccount.phone_number == User.phone_number).subquery()


@router.get("/users")
async def users(q: str = Query("", max_length=128), stage: Stage | None = None,
                plan: Literal["free", "pro", "max", "business"] | None = None,
                limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    view = user_view()
    filters = []
    if q.strip():
        escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        filters.append(or_(view.c.name.ilike(f"%{escaped}%", escape="\\"), view.c.phone_number.ilike(f"%{escaped}%", escape="\\")))
    if stage:
        filters.append(view.c.stage == stage)
    if plan:
        filters.append(view.c.plan_tier == plan)
    async with async_session() as db:
        total = await db.scalar(select(func.count()).select_from(view).where(*filters))
        rows = (await db.execute(select(view).where(*filters).order_by(view.c.created_at.desc(), view.c.id.desc()).limit(limit).offset(offset))).mappings().all()
    return {"items": [dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/users/{user_id}")
async def user_detail(user_id: int):
    view = user_view()
    async with async_session() as db:
        row = (await db.execute(select(view).where(view.c.id == user_id))).mappings().first()
        if row is None:
            raise HTTPException(404, "User not found")
        setup = await db.get(UserOnboarding, user_id)
        usage = (await db.execute(select(UserUsage.date, UserUsage.query_count).where(UserUsage.user_id == user_id).order_by(UserUsage.date.desc()).limit(30))).mappings().all()
        connections = (await db.execute(select(UserConnection.toolkit, UserConnection.status, UserConnection.updated_at).where(UserConnection.phone_number == row["phone_number"]))).mappings().all()
        actions = (await db.execute(select(ToolRun.toolkit, ToolRun.tool_slug, ToolRun.status, ToolRun.created_at).where(ToolRun.phone_number == row["phone_number"]).order_by(ToolRun.created_at.desc()).limit(30))).mappings().all()
        events = (await db.execute(select(ActivityEvent.intent, ActivityEvent.emotion, ActivityEvent.created_at).where(ActivityEvent.phone_number == row["phone_number"]).order_by(ActivityEvent.created_at.desc()).limit(30))).mappings().all()
    return dict(row) | {"interests": setup.interests if setup else [], "usage": [dict(r) for r in usage],
                        "connections": [dict(r) for r in connections], "actions": [dict(r) for r in actions], "events": [dict(r) for r in events]}


@router.get("/overview")
async def overview():
    view = user_view()
    since = datetime.utcnow() - timedelta(hours=24)
    async with async_session() as db:
        total = await db.scalar(select(func.count(User.id))) or 0
        today = await db.scalar(select(func.sum(UserUsage.query_count)).where(UserUsage.date == date.today())) or 0
        active = await db.scalar(select(func.count(UserUsage.id)).where(UserUsage.date == date.today(), UserUsage.query_count > 0)) or 0
        stages = (await db.execute(select(view.c.stage, func.count().label("count")).group_by(view.c.stage))).mappings().all()
        flows = dict((await db.execute(select(FlowLog.status, func.count()).where(FlowLog.created_at >= since).group_by(FlowLog.status))).all())
        new = await db.scalar(select(func.count(User.id)).where(User.created_at >= since)) or 0
    success, errors = flows.get("success", 0), flows.get("error", 0)
    return {"total_users": total, "today_queries": today, "active_today": active, "new_users_24h": new,
            "stages": [dict(r) for r in stages], "flows_24h": flows,
            "success_percent": round(100 * success / (success + errors), 1) if success + errors else None,
            "timezone": "UTC", "generated_at": datetime.utcnow()}


@router.get("/analytics")
async def analytics(days: int = Query(30, ge=1, le=90)):
    start = date.today() - timedelta(days=days - 1)
    since = datetime.combine(start, datetime.min.time())
    async with async_session() as db:
        daily = (await db.execute(select(UserUsage.date, func.sum(UserUsage.query_count).label("queries"), func.count().label("active_users")).where(UserUsage.date >= start, UserUsage.query_count > 0).group_by(UserUsage.date).order_by(UserUsage.date))).mappings().all()
        intents = (await db.execute(select(ActivityEvent.intent.label("label"), func.count().label("count")).where(ActivityEvent.created_at >= since).group_by(ActivityEvent.intent).order_by(func.count().desc()).limit(20))).mappings().all()
        emotions = (await db.execute(select(ActivityEvent.emotion.label("label"), func.count().label("count")).where(ActivityEvent.created_at >= since).group_by(ActivityEvent.emotion).order_by(func.count().desc()))).mappings().all()
        models = (await db.execute(select(ModelCall.model, ModelCall.route, ModelCall.status, func.count().label("calls"), func.avg(ModelCall.latency_ms).label("latency_ms"), func.sum(ModelCall.input_tokens).label("input_tokens"), func.sum(ModelCall.output_tokens).label("output_tokens")).where(ModelCall.created_at >= since).group_by(ModelCall.model, ModelCall.route, ModelCall.status))).mappings().all()
        connectors = (await db.execute(select(UserConnection.toolkit.label("label"), func.count().label("count")).where(UserConnection.status == "active").group_by(UserConnection.toolkit).order_by(func.count().desc()))).mappings().all()
        tools = (await db.execute(select(ToolRun.status.label("label"), func.count().label("count")).where(ToolRun.created_at >= since).group_by(ToolRun.status))).mappings().all()
    by_date = {r["date"]: dict(r) for r in daily}
    series = [by_date.get(start + timedelta(days=i), {"date": start + timedelta(days=i), "queries": 0, "active_users": 0}) for i in range(days)]
    return {"days": days, "timezone": "UTC", "daily": series, "intents": [dict(r) for r in intents],
            "emotions": [dict(r) for r in emotions], "models": [dict(r) for r in models],
            "connectors": [dict(r) for r in connectors], "tools": [dict(r) for r in tools],
            "telemetry_note": "Model calls and intent/emotion events are recorded from the admin release onward. Token counts are provider-reported; billing costs are not available."}


@router.get("/config")
async def config():
    return await read_config()


class ConfigPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, strict=True)
    values: dict = Field(min_length=1, max_length=10)


@router.patch("/config")
async def save_config(body: ConfigPatch):
    current = await read_config()
    try:
        validated = RuntimeValues.model_validate(current["values"] | body.values).model_dump()
    except ValidationError:
        raise HTTPException(422, "Invalid settings: use supported models and the displayed value ranges")
    changes = {key: {"before": current["values"][key], "after": value} for key, value in validated.items() if current["values"][key] != value}
    async with async_session() as db:
        changed = await db.execute(update(RuntimeConfig).where(RuntimeConfig.id == 1, RuntimeConfig.revision == body.revision).values(values=validated, revision=body.revision + 1, updated_at=datetime.utcnow()))
        if changed.rowcount != 1:
            raise HTTPException(409, "Settings changed in another session. Reload before saving.")
        db.add(AdminAudit(action="config.updated", changes=changes))
        await db.commit()
    return await read_config()


@router.get("/models")
async def models():
    return {"provider": "Google Gemini", "models": [{"id": model, "thinking": "minimal" if "lite" in model else "low"} for model in MODELS],
            "strategy": "JSON classification → fast replies for simple tasks; reply model for complex tasks → one fast-model retry on reply failure/timeout",
            "reply_timeout_seconds": 10, "total_timeout_seconds": 20}


@router.get("/audit")
async def audit(limit: int = Query(50, ge=1, le=200)):
    async with async_session() as db:
        rows = (await db.execute(select(AdminAudit).order_by(AdminAudit.id.desc()).limit(limit))).scalars().all()
    return [{"id": r.id, "action": r.action, "changes": r.changes, "created_at": r.created_at} for r in rows]


@router.get("/flows")
async def flows(status: Literal["success", "error", "ignored"] | None = None,
                limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0, le=100000)):
    query = select(FlowLog)
    if status:
        query = query.where(FlowLog.status == status)
    async with async_session() as db:
        rows = (await db.execute(query.order_by(FlowLog.id.desc()).limit(limit).offset(offset))).scalars().all()
    # Payloads contain private messages/provider details; keep the operational feed metadata-only.
    return [{"id": r.id, "direction": r.direction, "sender": r.sender, "status": r.status,
             "has_error": bool(r.error_message), "created_at": r.created_at} for r in rows]


@router.get("/integrations")
async def integrations():
    settings = get_settings()
    return {"environment": settings.ENVIRONMENT, "services": {
        "Gemini": bool(settings.GEMINI_API_KEY), "WhatsApp": bool(settings.WHATSAPP_TOKEN and settings.WHATSAPP_APP_SECRET),
        "Composio": bool(settings.COMPOSIO_API_KEY),
        **({"Polar": bool(settings.POLAR_ACCESS_TOKEN)} if hasattr(settings, "POLAR_ACCESS_TOKEN") else
           {"Razorpay": bool(getattr(settings, "RAZORPAY_KEY_ID", "") and getattr(settings, "RAZORPAY_KEY_SECRET", ""))})},
        "configured_toolkits": sorted(settings.COMPOSIO_AUTH_CONFIGS),
        "note": "Configured indicates credentials are present, not a live provider health check. Secrets and connector versions are managed in the deployment environment."}
