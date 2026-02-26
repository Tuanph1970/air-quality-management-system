"""Sensor repository interface (port).

Defines the abstract contract for persisting and retrieving ``Sensor``
aggregates.  Concrete implementations live in the infrastructure layer.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.sensor import Sensor


class SensorRepository(ABC):
    """Abstract repository for ``Sensor`` aggregate persistence."""

    @abstractmethod
    async def get_by_id(self, sensor_id: UUID) -> Optional[Sensor]:
        """Return a sensor by its unique ID, or ``None``."""

    @abstractmethod
    async def get_by_serial_number(self, serial_number: str) -> Optional[Sensor]:
        """Return a sensor by its serial number, or ``None``."""

    @abstractmethod
    async def list_by_factory(
        self,
        factory_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Sensor]:
        """Return sensors for a factory, optionally filtered by status."""

    @abstractmethod
    async def list_all(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Sensor]:
        """Return a paginated list of sensors, optionally filtered."""

    @abstractmethod
    async def save(self, sensor: Sensor) -> Sensor:
        """Persist a new or updated sensor and return it."""

    @abstractmethod
    async def delete(self, sensor_id: UUID) -> bool:
        """Delete a sensor by ID.  Return ``True`` if it existed."""

    @abstractmethod
    async def count(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        """Return the total number of sensors, optionally filtered."""
