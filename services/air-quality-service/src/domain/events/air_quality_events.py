"""Air quality domain events."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class AQICalculated:
    location_lat: float = 0.0
    location_lng: float = 0.0
    aqi_value: int = 0
    level: str = ""


@dataclass
class AQIThresholdExceeded:
    factory_id: UUID = None
    aqi_value: int = 0
    threshold: int = 0
