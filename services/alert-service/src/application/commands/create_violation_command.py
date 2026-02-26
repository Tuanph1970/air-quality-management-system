"""Command to create a violation."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreateViolationCommand:
    """Data required to create a new threshold violation."""

    factory_id: UUID
    sensor_id: UUID
    pollutant: str
    measured_value: float
    permitted_value: float
    severity: str
