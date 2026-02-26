"""Query to get a sensor by ID."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class GetSensorQuery:
    sensor_id: UUID
