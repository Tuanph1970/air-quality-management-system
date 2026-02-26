"""Violation repository interface (port).

Defines the persistence contract for ``Violation`` aggregates.  The
domain layer depends on this abstraction; the infrastructure layer
provides a concrete implementation (e.g. ``SQLAlchemyViolationRepository``).

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..entities.violation import Violation


class ViolationRepository(ABC):
    """Abstract repository for Violation aggregate persistence."""

    @abstractmethod
    async def get_by_id(self, violation_id: UUID) -> Optional[Violation]:
        """Retrieve a violation by its unique identifier.

        Returns ``None`` if not found.
        """

    @abstractmethod
    async def list_by_factory(
        self,
        factory_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        """List violations for a specific factory.

        Parameters
        ----------
        factory_id:
            The factory to filter by.
        status:
            Optional status filter ("OPEN" or "RESOLVED").
        skip:
            Number of records to skip (pagination offset).
        limit:
            Maximum records to return.
        """

    @abstractmethod
    async def list_open(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        """List all currently open (unresolved) violations."""

    @abstractmethod
    async def list_by_sensor(
        self,
        sensor_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        """List violations originating from a specific sensor."""

    @abstractmethod
    async def list_by_severity(
        self,
        severity: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Violation]:
        """List violations of a given severity level."""

    @abstractmethod
    async def count(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count violations with optional filters."""

    @abstractmethod
    async def save(self, violation: Violation) -> Violation:
        """Persist a violation (insert or update)."""

    @abstractmethod
    async def delete(self, violation_id: UUID) -> bool:
        """Delete a violation by ID.  Returns True if deleted."""
