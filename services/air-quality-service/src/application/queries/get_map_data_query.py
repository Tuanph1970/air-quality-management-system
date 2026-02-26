"""Query to get map visualization data."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetMapDataQuery:
    center_lat: float = 0.0
    center_lng: float = 0.0
    radius_km: float = 50.0
    pollutant: Optional[str] = None
