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
