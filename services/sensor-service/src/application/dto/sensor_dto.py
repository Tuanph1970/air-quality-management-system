"""Sensor data transfer objects."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class SensorDTO:
    id: UUID
    factory_id: UUID
    sensor_type: str
    latitude: float
    longitude: float
    status: str
    last_calibration: Optional[datetime]

    @classmethod
    def from_entity(cls, entity) -> "SensorDTO":
        pass


@dataclass
class ReadingDTO:
    id: UUID
    sensor_id: UUID
    pm25: float
    pm10: float
    co: float
    no2: float
    so2: float
    o3: float
    aqi: int
    timestamp: datetime

    @classmethod
    def from_entity(cls, entity) -> "ReadingDTO":
        pass
