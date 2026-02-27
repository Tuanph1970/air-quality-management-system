"""User repository interface (port).

Defines the persistence contract for User aggregates. The domain layer
depends on this abstraction; the infrastructure layer provides the
concrete implementation.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.user import User


class UserRepository(ABC):
    """Abstract repository for User aggregate persistence."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Retrieve a user by their unique identifier.

        Returns ``None`` if not found.
        """

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address.

        Returns ``None`` if not found.
        """

    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[User]:
        """List users with optional filters and pagination."""

    @abstractmethod
    async def count(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count users with optional filters."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist a user (insert or update)."""

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete a user by ID. Returns True if deleted."""

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
