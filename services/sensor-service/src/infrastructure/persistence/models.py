"""SQLAlchemy models for sensor service."""
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()


class SensorModel(Base):
    __tablename__ = "sensors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factory_id = Column(UUID(as_uuid=True), nullable=False)
    sensor_type = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), default="ACTIVE")
    last_calibration = Column(DateTime, nullable=True)
    installed_at = Column(DateTime, default=datetime.utcnow)


class ReadingModel(Base):
    __tablename__ = "readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id = Column(UUID(as_uuid=True), nullable=False)
    factory_id = Column(UUID(as_uuid=True), nullable=False)
    pm25 = Column(Float, default=0.0)
    pm10 = Column(Float, default=0.0)
    co = Column(Float, default=0.0)
    no2 = Column(Float, default=0.0)
    so2 = Column(Float, default=0.0)
    o3 = Column(Float, default=0.0)
    aqi = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
