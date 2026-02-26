"""Query to get a sensor by ID."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class GetSensorQuery:
    """Query to retrieve a single sensor by ID."""

    sensor_id: UUID

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if self.sensor_id is None:
            raise ValueError("sensor_id is required")


@dataclass(frozen=True)
class ListSensorsQuery:
    """Query to list sensors with optional filters and pagination."""

    factory_id: Optional[UUID] = None
    status: Optional[str] = None
    skip: int = 0
    limit: int = 20

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if self.skip < 0:
            raise ValueError("skip must be non-negative")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("limit must be between 1 and 100")
