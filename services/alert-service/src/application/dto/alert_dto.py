"""Alert data transfer objects."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ViolationDTO:
    id: UUID
    factory_id: UUID
    pollutant: str
    measured_value: float
    threshold: float
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime]

    @classmethod
    def from_entity(cls, entity) -> "ViolationDTO":
        pass
