"""Factory data transfer objects.

DTOs decouple the domain model from the interface layer.  The application
service always returns DTOs — never raw domain entities.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from ...domain.entities.factory import Factory


@dataclass
class FactoryDTO:
    """Flat, serialisation-friendly representation of a Factory entity."""

    id: UUID
    name: str
    registration_number: str
    industry_type: str
    latitude: float
    longitude: float
    emission_limits: Dict[str, float]
    status: str
    created_at: datetime
    updated_at: datetime

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_entity(cls, entity: Factory) -> FactoryDTO:
        """Map a domain ``Factory`` entity to a DTO."""
        return cls(
            id=entity.id,
            name=entity.name,
            registration_number=entity.registration_number,
            industry_type=entity.industry_type,
            latitude=entity.location.latitude,
            longitude=entity.location.longitude,
            emission_limits=entity.emission_limits.to_dict(),
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary suitable for JSON serialisation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "registration_number": self.registration_number,
            "industry_type": self.industry_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "emission_limits": self.emission_limits,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class FactoryListDTO:
    """Paginated list of factory DTOs with total count."""

    items: List[FactoryDTO]
    total: int
    skip: int
    limit: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [f.to_dict() for f in self.items],
            "total": self.total,
            "skip": self.skip,
            "limit": self.limit,
        }
