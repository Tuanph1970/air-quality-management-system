"""Air Quality Index entity."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict
from uuid import UUID, uuid4


@dataclass
class AirQualityIndex:
    """AQI Entity."""

    id: UUID = field(default_factory=uuid4)
    location_lat: float = 0.0
    location_lng: float = 0.0
    aqi_value: int = 0
    level: str = "GOOD"
    pollutants: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
