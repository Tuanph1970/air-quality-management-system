"""SQLAlchemy models for alert service."""
from sqlalchemy import Column, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()


class ViolationModel(Base):
    __tablename__ = "violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factory_id = Column(UUID(as_uuid=True), nullable=False)
    pollutant = Column(String(20), nullable=False)
    measured_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), default="LOW")
    status = Column(String(20), default="OPEN")
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)


class AlertConfigModel(Base):
    __tablename__ = "alert_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pollutant = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), default="LOW")
    is_active = Column(Boolean, default=True)
