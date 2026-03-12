"""SQLAlchemy models for station ingestion database."""
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class StationModel(Base):
    """Database model for monitoring stations."""

    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    station_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    station_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    station_type: Mapped[int] = mapped_column(Integer, nullable=True)
    province_id: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    station_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    readings: Mapped[list["AirQualityReadingModel"]] = relationship(
        "AirQualityReadingModel", back_populates="station", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Station(id={self.id}, code={self.station_code}, name={self.station_name})>"


class AirQualityReadingModel(Base):
    """Database model for air quality readings."""

    __tablename__ = "air_quality_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    station_code: Mapped[str] = mapped_column(
        String(100), ForeignKey("stations.station_code"), nullable=False, index=True
    )
    reading_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    aqi: Mapped[float] = mapped_column(Float, nullable=True)
    pm25: Mapped[float] = mapped_column(Float, nullable=True)
    pm10: Mapped[float] = mapped_column(Float, nullable=True)
    co: Mapped[float] = mapped_column(Float, nullable=True)
    so2: Mapped[float] = mapped_column(Float, nullable=True)
    no2: Mapped[float] = mapped_column(Float, nullable=True)
    o3: Mapped[float] = mapped_column(Float, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)
    humidity: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    station: Mapped["StationModel"] = relationship("StationModel", back_populates="readings")

    # Index for efficient time-based queries
    __table_args__ = (
        Index("idx_station_time", "station_code", "reading_time"),
    )

    def __repr__(self) -> str:
        return f"<AirQualityReading(id={self.id}, station={self.station_code}, time={self.reading_time})>"


def create_tables(database_url: str) -> None:
    """Create database tables.

    Args:
        database_url: Database connection URL
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)


def get_session(database_url: str) -> Session:
    """Get database session.

    Args:
        database_url: Database connection URL

    Returns:
        SQLAlchemy session
    """
    engine = create_engine(database_url, echo=False)
    return Session(engine)
