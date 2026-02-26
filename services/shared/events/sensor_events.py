"""Sensor domain events shared across services.

Published by the Sensor Service.  SensorReadingCreated is the primary
event that drives the Alert Service threshold checks and Air Quality
Service AQI recalculations.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from .base_event import DomainEvent


@dataclass
class SensorRegistered(DomainEvent):
    """A new sensor has been installed and registered."""

    sensor_id: UUID = None
    factory_id: UUID = None
    sensor_type: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    event_type: str = "sensor.registered"


@dataclass
class SensorReadingCreated(DomainEvent):
    """A sensor has submitted a new air-quality reading.

    This is the highest-volume event in the system.  The Alert Service
    listens for it to check threshold violations, and the Air Quality
    Service uses it to refresh cached AQI values.
    """

    sensor_id: UUID = None
    factory_id: UUID = None
    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0
    no2: float = 0.0
    so2: float = 0.0
    o3: float = 0.0
    aqi: int = 0
    reading_timestamp: Optional[datetime] = None
    event_type: str = "sensor.reading.created"


@dataclass
class SensorCalibrated(DomainEvent):
    """A sensor has been recalibrated."""

    sensor_id: UUID = None
    calibrated_by: UUID = None
    offset: float = 0.0
    scale_factor: float = 1.0
    event_type: str = "sensor.calibrated"


@dataclass
class SensorStatusChanged(DomainEvent):
    """A sensor's operational status has changed (e.g. ACTIVE -> OFFLINE)."""

    sensor_id: UUID = None
    factory_id: UUID = None
    old_status: str = ""
    new_status: str = ""
    reason: str = ""
    event_type: str = "sensor.status.changed"
