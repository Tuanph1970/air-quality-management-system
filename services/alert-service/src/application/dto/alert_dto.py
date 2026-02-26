"""Alert data transfer objects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ...domain.entities.violation import Violation


@dataclass
class ViolationDTO:
    """Read-only projection of a Violation entity for the interface layer."""

    id: UUID
    factory_id: UUID
    sensor_id: UUID
    pollutant: str
    measured_value: float
    permitted_value: float
    exceedance_percentage: float
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    action_taken: str
    notes: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Violation) -> ViolationDTO:
        """Map a domain entity to a DTO."""
        return cls(
            id=entity.id,
            factory_id=entity.factory_id,
            sensor_id=entity.sensor_id,
            pollutant=entity.pollutant,
            measured_value=entity.measured_value,
            permitted_value=entity.permitted_value,
            exceedance_percentage=entity.exceedance_percentage,
            severity=entity.severity.value if hasattr(entity.severity, "value") else str(entity.severity),
            status=entity.status,
            detected_at=entity.detected_at,
            resolved_at=entity.resolved_at,
            action_taken=entity.action_taken,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
