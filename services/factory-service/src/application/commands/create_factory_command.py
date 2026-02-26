"""Command to create a new factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class CreateFactoryCommand:
    """Immutable command carrying all data needed to register a factory.

    Validated by the application service before domain entity creation.
    """

    name: str
    registration_number: str
    industry_type: str
    latitude: float
    longitude: float
    emission_limits: Dict = field(default_factory=dict)

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid."""
        if not self.name or not self.name.strip():
            raise ValueError("Factory name is required")
        if not self.registration_number or not self.registration_number.strip():
            raise ValueError("Registration number is required")
        if not self.industry_type or not self.industry_type.strip():
            raise ValueError("Industry type is required")
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")
