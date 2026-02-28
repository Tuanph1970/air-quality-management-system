"""SQLAlchemy ORM models for the factory service.

These models define the relational schema that backs the ``Factory`` and
``Suspension`` domain entities.  Mapping between ORM models and domain
objects is handled by the repository implementation — the domain layer
never imports this module directly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FactoryModel(Base):
    """Relational representation of a Factory aggregate root."""

    __tablename__ = "factories"

    # --- identity ---
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    # --- core fields ---
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
    )
    industry_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # --- location ---
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # --- emissions ---
    emission_limits: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
    )

    # --- status ---
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE",
    )

    # --- timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow,
    )

    # --- relationships ---
    suspensions: Mapped[list["SuspensionModel"]] = relationship(
        back_populates="factory",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SuspensionModel.suspended_at.desc()",
    )

    # --- indexes ---
    __table_args__ = (
        Index("ix_factories_status", "status"),
        Index("ix_factories_industry_type", "industry_type"),
        Index("ix_factories_registration_number", "registration_number", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<FactoryModel id={self.id} name={self.name!r} "
            f"status={self.status}>"
        )


class SuspensionModel(Base):
    """Relational representation of a Suspension entity."""

    __tablename__ = "suspensions"

    # --- identity ---
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    # --- foreign key ---
    factory_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- core fields ---
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    suspended_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False,
    )
    suspended_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    # --- resume fields ---
    resumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    resumed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True,
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # --- status ---
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
    )

    # --- relationships ---
    factory: Mapped["FactoryModel"] = relationship(back_populates="suspensions")

    # --- indexes ---
    __table_args__ = (
        Index("ix_suspensions_factory_id", "factory_id"),
        Index("ix_suspensions_is_active", "is_active"),
        Index(
            "ix_suspensions_factory_active",
            "factory_id",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SuspensionModel id={self.id} factory_id={self.factory_id} "
            f"active={self.is_active}>"
        )
