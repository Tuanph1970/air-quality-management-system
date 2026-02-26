"""SQLAlchemy models for factory service."""
from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()


class FactoryModel(Base):
    __tablename__ = "factories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100), unique=True, nullable=False)
    industry_type = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    max_emissions = Column(JSON, default={})
    operational_status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SuspensionModel(Base):
    __tablename__ = "suspensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factory_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(String(500), nullable=False)
    suspended_by = Column(UUID(as_uuid=True), nullable=False)
    suspended_at = Column(DateTime, default=datetime.utcnow)
    resumed_at = Column(DateTime, nullable=True)
    is_active = Column(String(5), default="true")
