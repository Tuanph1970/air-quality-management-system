"""Query to get a factory by ID."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetFactoryQuery:
    """Query to retrieve a single factory by its unique identifier."""

    factory_id: UUID
