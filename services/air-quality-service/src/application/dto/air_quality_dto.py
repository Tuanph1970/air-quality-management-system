"""Air quality data transfer objects."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class AirQualityDTO:
    aqi_value: int
    level: str
    pollutants: Dict
    latitude: float
    longitude: float
    timestamp: datetime

    @classmethod
    def from_entity(cls, entity) -> "AirQualityDTO":
        pass
