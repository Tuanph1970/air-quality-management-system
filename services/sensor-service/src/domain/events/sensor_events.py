"""Sensor domain events."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class SensorRegistered:
    sensor_id: UUID = None
    factory_id: UUID = None


@dataclass
class SensorReadingCreated:
    sensor_id: UUID = None
    factory_id: UUID = None
    pm25: float = 0.0
    pm10: float = 0.0
    aqi: int = 0
    timestamp: datetime = None


@dataclass
class SensorCalibrated:
    sensor_id: UUID = None
