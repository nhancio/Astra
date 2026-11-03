"""Durable operational configuration, change history and content-free LLM telemetry."""
from sqlalchemy import Column, DateTime, Integer, JSON, String, func
from app.models.database import Base


class RuntimeConfig(Base):
    __tablename__ = "runtime_config"
    id = Column(Integer, primary_key=True)
    revision = Column(Integer, nullable=False, default=1)
    values = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class AdminAudit(Base):
    __tablename__ = "admin_audit"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(64), nullable=False)
    changes = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ModelCall(Base):
    __tablename__ = "model_calls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(100), nullable=False)
    route = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False)
    latency_ms = Column(Integer, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class ActivityEvent(Base):
    __tablename__ = "activity_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False, index=True)
    intent = Column(String(64), nullable=False)
    emotion = Column(String(32), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
