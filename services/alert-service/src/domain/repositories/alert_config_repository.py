"""Alert configuration repository interface (port).

Defines the persistence contract for ``AlertConfig`` entities.  The
domain layer depends on this abstraction; the infrastructure layer
provides a concrete implementation.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.alert_config import AlertConfig


class AlertConfigRepository(ABC):
    """Abstract repository for AlertConfig entity persistence."""

    @abstractmethod
    async def get_by_id(self, config_id: UUID) -> Optional[AlertConfig]:
        """Retrieve an alert config by its unique identifier."""

    @abstractmethod
    async def get_by_pollutant(self, pollutant: str) -> Optional[AlertConfig]:
        """Retrieve the active config for a specific pollutant."""

    @abstractmethod
    async def list_active(self) -> List[AlertConfig]:
        """List all active alert configurations."""

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[AlertConfig]:
        """List all alert configurations with pagination."""

    @abstractmethod
    async def save(self, config: AlertConfig) -> AlertConfig:
        """Persist an alert config (insert or update)."""

    @abstractmethod
    async def delete(self, config_id: UUID) -> bool:
        """Delete an alert config by ID.  Returns True if deleted."""
