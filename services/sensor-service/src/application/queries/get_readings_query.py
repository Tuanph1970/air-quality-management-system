"""Query to get sensor readings with time range and aggregation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class GetReadingsQuery:
    """Query to retrieve readings with optional filters and time range.

    Supports filtering by sensor, factory, and time range.
    """

    sensor_id: Optional[UUID] = None
    factory_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = 0
    limit: int = 100

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if self.sensor_id is None and self.factory_id is None:
            raise ValueError("At least one of sensor_id or factory_id is required")
        if self.skip < 0:
            raise ValueError("skip must be non-negative")
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.start_time >= self.end_time
        ):
            raise ValueError("start_time must be before end_time")


@dataclass(frozen=True)
class GetReadingAverageQuery:
    """Query to get averaged readings over a time range."""

    sensor_id: UUID
    start_time: datetime
    end_time: datetime

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if self.sensor_id is None:
            raise ValueError("sensor_id is required")
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
