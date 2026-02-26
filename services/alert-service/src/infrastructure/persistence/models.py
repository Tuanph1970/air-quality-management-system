"""SQLAlchemy ORM models for the alert service.

Maps domain entities to database tables.  These models are the only
place that knows about column types and table names — the domain layer
remains free of persistence concerns.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ViolationModel(Base):
    """Persistence model for the ``violations`` table."""

    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    factory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    sensor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    pollutant: Mapped[str] = mapped_column(String(20), nullable=False)
    measured_value: Mapped[float] = mapped_column(Float, nullable=False)
    permitted_value: Mapped[float] = mapped_column(Float, nullable=False)
    exceedance_percentage: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="WARNING"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="OPEN", index=True
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    action_taken: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_violations_factory_status", "factory_id", "status"),
        Index("ix_violations_severity", "severity"),
    )


class AlertConfigModel(Base):
    """Persistence model for the ``alert_configs`` table."""

    __tablename__ = "alert_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    pollutant: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    warning_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    high_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    critical_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    notify_email: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    notify_sms: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
