"""SQLAlchemy models for station service."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON, VARCHAR
from sqlalchemy.orm import relationship
from uuid import uuid4

from .database import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())


class StationModel(Base):
    """SQLAlchemy model for air quality stations."""
    
    __tablename__ = "stations"
    
    # Primary key
    id = Column(VARCHAR(36), primary_key=True, default=generate_uuid)
    
    # Identity
    station_code = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Classification
    station_type = Column(String(50), nullable=False, default="URBAN")
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=False, index=True)
    
    # API Configuration (stored as JSON)
    api_config = Column(JSON, nullable=True)
    
    # Data retention
    data_retention_days = Column(Integer, default=1, nullable=False)
    
    # Metadata (named station_metadata to avoid conflict with SQLAlchemy reserved attribute)
    station_metadata = Column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_data_received = Column(DateTime, nullable=True)
    
    # Relationships
    readings = relationship(
        "PollutantReadingModel",
        back_populates="station",
        cascade="all, delete-orphan",
        lazy="select",
    )
    raw_data = relationship(
        "RawStationDataModel",
        back_populates="station",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_station_location", "latitude", "longitude"),
        Index("idx_station_active_type", "is_active", "station_type"),
    )
    
    def __repr__(self) -> str:
        return f"<Station(id={self.id}, code={self.station_code}, name={self.name})>"


class PollutantReadingModel(Base):
    """SQLAlchemy model for pollutant readings (time-series data)."""

    __tablename__ = "pollutant_readings"

    # Primary key
    id = Column(VARCHAR(36), primary_key=True, default=generate_uuid)

    # Foreign key
    station_id = Column(
        VARCHAR(36),
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Pollutant info
    pollutant_type = Column(String(20), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False, default="µg/m³")

    # Quality
    quality_flag = Column(String(20), nullable=True)

    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    station = relationship("StationModel", back_populates="readings")

    # Indexes for efficient time-series queries
    __table_args__ = (
        Index("idx_reading_station_time", "station_id", "timestamp"),
        Index("idx_reading_time_pollutant", "timestamp", "pollutant_type"),
        UniqueConstraint("station_id", "timestamp", "pollutant_type", name="uq_station_time_pollutant"),
    )

    def __repr__(self) -> str:
        return f"<PollutantReading(station_id={self.station_id}, type={self.pollutant_type}, value={self.value})>"


class RawStationDataModel(Base):
    """SQLAlchemy model for raw 5-minute interval station data from EnviSoft.

    This stores the complete raw data as received from EnviSoft API including
    all pollutant measurements, environmental data, and wind information.
    """

    __tablename__ = "raw_station_data"

    # Primary key
    id = Column(VARCHAR(36), primary_key=True, default=generate_uuid)

    # Foreign key to station
    station_id = Column(
        VARCHAR(36),
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Time data was measured (from EnviSoft)
    measured_at = Column(DateTime, nullable=False, index=True)

    # Pollutant measurements
    no_value = Column(Float, nullable=True)
    o3_value = Column(Float, nullable=True)
    co_value = Column(Float, nullable=True)
    no2_value = Column(Float, nullable=True)
    nox_value = Column(Float, nullable=True)
    so2_value = Column(Float, nullable=True)
    pm10_value = Column(Float, nullable=True)
    pm25_value = Column(Float, nullable=True)

    # Environmental data
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)

    # Wind data
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)

    # Additional fields from EnviSoft
    aqi = Column(Float, nullable=True)
    aqi_category = Column(String(50), nullable=True)

    # Source tracking
    source = Column(String(50), nullable=False, default="ENVISOFT_API")
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Store complete raw response for debugging/audit
    raw_data = Column(JSON, nullable=True)

    # Relationships
    station = relationship("StationModel", back_populates="raw_data")

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_raw_station_time", "station_id", "measured_at"),
        Index("idx_raw_measured_at", "measured_at"),
        UniqueConstraint("station_id", "measured_at", name="uq_raw_station_measured"),
    )

    def __repr__(self) -> str:
        return f"<RawStationData(station_id={self.station_id}, measured_at={self.measured_at})>"
