"""Reading data transfer objects.

DTOs decouple the domain model from the interface layer.  The application
service always returns DTOs — never raw domain entities.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...domain.entities.reading import Reading


@dataclass
class ReadingDTO:
    """Flat, serialisation-friendly representation of a Reading entity."""

    id: UUID
    sensor_id: UUID
    factory_id: Optional[UUID]
    pm25: float
    pm10: float
    co: float
    co2: float
    no2: float
    nox: float
    so2: float
    o3: float
    temperature: float
    humidity: float
    aqi: int
    timestamp: datetime

    @classmethod
    def from_entity(cls, entity: Reading) -> ReadingDTO:
        """Map a domain ``Reading`` entity to a DTO."""
        return cls(
            id=entity.id,
            sensor_id=entity.sensor_id,
            factory_id=entity.factory_id,
            pm25=entity.pm25,
            pm10=entity.pm10,
            co=entity.co,
            co2=entity.co2,
            no2=entity.no2,
            nox=entity.nox,
            so2=entity.so2,
            o3=entity.o3,
            temperature=entity.temperature,
            humidity=entity.humidity,
            aqi=entity.aqi,
            timestamp=entity.timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary suitable for JSON serialisation."""
        return {
            "id": str(self.id),
            "sensor_id": str(self.sensor_id),
            "factory_id": str(self.factory_id) if self.factory_id else None,
            "pm25": self.pm25,
            "pm10": self.pm10,
            "co": self.co,
            "co2": self.co2,
            "no2": self.no2,
            "nox": self.nox,
            "so2": self.so2,
            "o3": self.o3,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "aqi": self.aqi,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReadingListDTO:
    """Paginated list of reading DTOs with total count."""

    items: List[ReadingDTO]
    total: int
    skip: int
    limit: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [r.to_dict() for r in self.items],
            "total": self.total,
            "skip": self.skip,
            "limit": self.limit,
        }
