"""Factory repository interface (port)."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.factory import Factory


class FactoryRepository(ABC):
    """Repository Interface - defined in domain layer."""

    @abstractmethod
    async def get_by_id(self, factory_id: UUID) -> Optional[Factory]:
        pass

    @abstractmethod
    async def get_by_registration_number(self, reg_number: str) -> Optional[Factory]:
        pass

    @abstractmethod
    async def list_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[Factory]:
        pass

    @abstractmethod
    async def save(self, factory: Factory) -> Factory:
        pass

    @abstractmethod
    async def delete(self, factory_id: UUID) -> bool:
        pass
