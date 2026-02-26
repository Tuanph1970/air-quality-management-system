"""Violation repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.violation import Violation


class ViolationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, violation_id: UUID) -> Optional[Violation]:
        pass

    @abstractmethod
    async def list_by_factory(self, factory_id: UUID) -> List[Violation]:
        pass

    @abstractmethod
    async def list_open(self) -> List[Violation]:
        pass

    @abstractmethod
    async def save(self, violation: Violation) -> Violation:
        pass
