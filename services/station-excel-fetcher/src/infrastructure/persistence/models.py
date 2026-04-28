"""SQLAlchemy models for station-excel-fetcher service."""

from __future__ import annotations

from datetime import date as date_type, datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Date,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EnvisoftHourlyReadingModel(Base):
    """SQLAlchemy model for hourly EnviSoft station readings.

    Stores pollutant measurements, AQI, environmental data, and wind data
    from the EnviSoft API for the 5 target stations.
    """

    __tablename__ = "envisoft_hourly_readings"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Station identity
    station_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    station_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    station_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Time
    measured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)")
    )

    # Pollutants (µg/m³)
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    no2: Mapped[float | None] = mapped_column(Float, nullable=True)
    so2: Mapped[float | None] = mapped_column(Float, nullable=True)
    co: Mapped[float | None] = mapped_column(Float, nullable=True)
    o3: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Air Quality Index
    aqi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aqi_category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Environmental
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Wind
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Additional
    no_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    nox_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_pollutant: Mapped[float | None] = mapped_column(Float, nullable=True)
    atmospheric_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    noise_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    radiation: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Excel reference path
    excel_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "station_id", "measured_at",
            name="uq_station_measured_at",
        ),
        Index("idx_station_measured_at", "station_id", "measured_at"),
        Index("idx_measured_at", "measured_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EnvisoftHourlyReading(station_id={self.station_id}, "
            f"measured_at={self.measured_at}, aqi={self.aqi})>"
        )


class EnvisoftFetchLogModel(Base):
    """SQLAlchemy model for fetch attempt logs.

    Tracks every fetch attempt so we can detect missing days and auto-retry.
    """

    __tablename__ = "envisoft_fetch_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # The date this fetch was FOR (not when it ran)
    fetch_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    # Which station was targeted
    station_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # Attempt number within this date+station (1 = first try)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # pending | success | partial | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # How many records were upserted this attempt
    records_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Human-readable error if failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When this attempt ran
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("(CURRENT_TIMESTAMP)")
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Which Excel file was used (if any)
    excel_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "fetch_date", "station_id", "attempt",
            name="uq_fetchlog_date_station_attempt",
        ),
        Index("idx_fetchlog_date_status", "fetch_date", "status"),
        Index("idx_fetchlog_date_station", "fetch_date", "station_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<EnvisoftFetchLog(date={self.fetch_date}, "
            f"station={self.station_id}, attempt={self.attempt}, status={self.status})>"
        )
