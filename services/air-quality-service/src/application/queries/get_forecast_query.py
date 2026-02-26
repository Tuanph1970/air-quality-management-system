"""Query to get AQI forecast."""
from dataclasses import dataclass


@dataclass
class GetForecastQuery:
    latitude: float
    longitude: float
    hours_ahead: int = 24
