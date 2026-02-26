"""Sensor reading entity."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Reading:
    """Reading Entity - sensor measurement record."""

    id: UUID = field(default_factory=uuid4)
    sensor_id: UUID = None
    factory_id: UUID = None
    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0
    no2: float = 0.0
    so2: float = 0.0
    o3: float = 0.0
    aqi: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
