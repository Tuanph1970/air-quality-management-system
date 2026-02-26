"""Reading repository interface (port).

Defines the abstract contract for persisting and querying ``Reading``
entities.  Optimised for time-series operations (TimescaleDB).

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..entities.reading import Reading


class ReadingRepository(ABC):
    """Abstract repository for ``Reading`` entity persistence."""

    @abstractmethod
    async def save(self, reading: Reading) -> Reading:
        """Persist a single reading and return it."""

    @abstractmethod
    async def save_batch(self, readings: List[Reading]) -> int:
        """Persist multiple readings in a single operation.

        Returns the number of readings successfully saved.
        """

    @abstractmethod
    async def get_readings(
        self,
        sensor_id: UUID,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> List[Reading]:
        """Return readings for a sensor within a time range.

        Ordered by ``timestamp`` descending (most recent first).
        """

    @abstractmethod
    async def get_latest(self, sensor_id: UUID) -> Optional[Reading]:
        """Return the most recent reading for a sensor, or ``None``."""

    @abstractmethod
    async def get_latest_by_factory(self, factory_id: UUID) -> Optional[Reading]:
        """Return the most recent reading from any sensor at a factory."""

    @abstractmethod
    async def get_average(
        self,
        sensor_id: UUID,
        start: datetime,
        end: datetime,
    ) -> Optional[Reading]:
        """Return an averaged reading over a time range, or ``None``."""

    @abstractmethod
    async def count(
        self,
        sensor_id: Optional[UUID] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> int:
        """Return the number of readings, optionally filtered."""
