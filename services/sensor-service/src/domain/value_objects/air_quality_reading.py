"""Air quality reading value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AirQualityReading:
    """Value Object for a single air quality measurement."""

    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0
    no2: float = 0.0
    so2: float = 0.0
    o3: float = 0.0
