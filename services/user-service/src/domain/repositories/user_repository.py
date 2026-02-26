"""User repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 20) -> List[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        pass
