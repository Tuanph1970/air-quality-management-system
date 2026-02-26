"""Command to create a violation."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreateViolationCommand:
    factory_id: UUID
    pollutant: str
    measured_value: float
    threshold: float
    severity: str
