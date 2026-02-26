"""Query to get factory emission data."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetFactoryEmissionsQuery:
    """Query to retrieve emission limit configuration for a factory."""

    factory_id: UUID
