"""Factory repository interface (port).

Defines the abstract persistence contract for the Factory aggregate root.
Implementations live in the infrastructure layer.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.factory import Factory


class FactoryRepository(ABC):
    """Abstract repository for Factory aggregate persistence.

    Concrete implementations (e.g. ``SQLAlchemyFactoryRepository``) reside
    in the infrastructure layer and are injected at application startup.
    """

    @abstractmethod
    async def get_by_id(self, factory_id: UUID) -> Optional[Factory]:
        """Return a factory by its unique ID, or ``None``."""

    @abstractmethod
    async def get_by_registration_number(self, reg_number: str) -> Optional[Factory]:
        """Return a factory by its registration number, or ``None``."""

    @abstractmethod
    async def list_all(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Factory]:
        """Return a paginated list of factories, optionally filtered by status."""

    @abstractmethod
    async def save(self, factory: Factory) -> Factory:
        """Persist a new or updated factory and return it."""

    @abstractmethod
    async def delete(self, factory_id: UUID) -> bool:
        """Delete a factory by ID.  Return ``True`` if it existed."""

    @abstractmethod
    async def count(self, status: Optional[str] = None) -> int:
        """Return the total number of factories, optionally filtered by status."""
