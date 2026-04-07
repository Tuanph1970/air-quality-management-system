"""SQLAlchemy models for station-excel-fetcher service."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
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
        DateTime, nullable=False, server_default=datetime.utcnow
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
