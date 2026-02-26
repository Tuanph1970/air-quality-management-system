"""Command to update an existing factory."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID


@dataclass(frozen=True)
class UpdateFactoryCommand:
    """Immutable command carrying partial update data for a factory.

    Only non-``None`` fields will be applied to the entity.
    """

    factory_id: UUID
    name: Optional[str] = None
    industry_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    emission_limits: Optional[Dict] = None

    def validate(self) -> None:
        """Raise ``ValueError`` if any provided field is invalid."""
        if self.name is not None and not self.name.strip():
            raise ValueError("Factory name cannot be blank")
        if self.industry_type is not None and not self.industry_type.strip():
            raise ValueError("Industry type cannot be blank")
        if self.latitude is not None and not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if self.longitude is not None and not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")

    def has_changes(self) -> bool:
        """Return ``True`` if at least one mutable field is set."""
        return any(
            getattr(self, f) is not None
            for f in ("name", "industry_type", "latitude", "longitude", "emission_limits")
        )
