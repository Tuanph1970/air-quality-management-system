"""Sensor data transfer objects.

DTOs decouple the domain model from the interface layer.  The application
service always returns DTOs — never raw domain entities.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...domain.entities.sensor import Sensor


@dataclass
class SensorDTO:
    """Flat, serialisation-friendly representation of a Sensor entity."""

    id: UUID
    serial_number: str
    sensor_type: str
    model: str
    factory_id: Optional[UUID]
    latitude: float
    longitude: float
    status: str
    last_calibration: Optional[datetime]
    installation_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Sensor) -> SensorDTO:
        """Map a domain ``Sensor`` entity to a DTO."""
        return cls(
            id=entity.id,
            serial_number=entity.serial_number,
            sensor_type=entity.sensor_type.value,
            model=entity.model,
            factory_id=entity.factory_id,
            latitude=entity.latitude,
            longitude=entity.longitude,
            status=entity.status.value,
            last_calibration=entity.last_calibration,
            installation_date=entity.installation_date,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary suitable for JSON serialisation."""
        return {
            "id": str(self.id),
            "serial_number": self.serial_number,
            "sensor_type": self.sensor_type,
            "model": self.model,
            "factory_id": str(self.factory_id) if self.factory_id else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "last_calibration": (
                self.last_calibration.isoformat() if self.last_calibration else None
            ),
            "installation_date": (
                self.installation_date.isoformat()
                if self.installation_date
                else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SensorListDTO:
    """Paginated list of sensor DTOs with total count."""

    items: List[SensorDTO]
    total: int
    skip: int
    limit: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [s.to_dict() for s in self.items],
            "total": self.total,
            "skip": self.skip,
            "limit": self.limit,
        }
