"""Reading repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..entities.reading import Reading


class ReadingRepository(ABC):
    @abstractmethod
    async def save(self, reading: Reading) -> Reading:
        pass

    @abstractmethod
    async def get_by_sensor(self, sensor_id: UUID, start: datetime, end: datetime) -> List[Reading]:
        pass

    @abstractmethod
    async def get_latest_by_factory(self, factory_id: UUID) -> Optional[Reading]:
        pass
