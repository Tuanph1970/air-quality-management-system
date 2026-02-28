"""SQLAlchemy ORM models for the sensor service.

These models define the relational schema that backs the ``Sensor`` and
``Reading`` domain entities.  The ``readings`` table is designed to be
converted into a TimescaleDB hypertable for efficient time-series queries.

Mapping between ORM models and domain objects is handled by the repository
implementation — the domain layer never imports this module directly.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .timescale_database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SensorModel(Base):
    """Relational representation of a Sensor aggregate root."""

    __tablename__ = "sensors"

    # --- identity ---
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    # --- core fields ---
    serial_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
    )
    sensor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    # --- association ---
    factory_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True,
    )

    # --- location ---
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # --- calibration ---
    calibration_params: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None,
    )

    # --- status ---
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ONLINE",
    )

    # --- timestamps ---
    installation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    last_calibration: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow,
    )

    # --- indexes ---
    __table_args__ = (
        Index("ix_sensors_serial_number", "serial_number", unique=True),
        Index("ix_sensors_factory_id", "factory_id"),
        Index("ix_sensors_status", "status"),
        Index("ix_sensors_sensor_type", "sensor_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<SensorModel id={self.id} serial={self.serial_number!r} "
            f"status={self.status}>"
        )


class ReadingModel(Base):
    """Relational representation of a Reading entity.

    Designed as a TimescaleDB hypertable — the ``timestamp`` column is the
    time dimension.  Create the hypertable after table creation::

        SELECT create_hypertable('readings', 'timestamp');
    """

    __tablename__ = "readings"

    # --- identity ---
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    # --- associations ---
    sensor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False,
    )
    factory_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True,
    )

    # --- pollutant concentrations ---
    pm25: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pm10: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    co: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    co2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    no2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nox: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    so2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    o3: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # --- environmental ---
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    humidity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # --- calculated ---
    aqi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- time dimension ---
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    # --- indexes ---
    # Note: TimescaleDB will auto-create indexes on the time dimension.
    # We add composite indexes for common query patterns.
    __table_args__ = (
        Index("ix_readings_sensor_id", "sensor_id"),
        Index("ix_readings_factory_id", "factory_id"),
        Index("ix_readings_timestamp", "timestamp"),
        Index(
            "ix_readings_sensor_timestamp",
            "sensor_id",
            "timestamp",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ReadingModel id={self.id} sensor={self.sensor_id} "
            f"aqi={self.aqi} ts={self.timestamp}>"
        )
