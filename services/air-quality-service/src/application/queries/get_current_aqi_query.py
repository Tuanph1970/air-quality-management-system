"""Query to get current AQI."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class GetCurrentAQIQuery:
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    factory_id: Optional[UUID] = None
