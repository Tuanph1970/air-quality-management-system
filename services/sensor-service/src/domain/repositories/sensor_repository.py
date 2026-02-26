"""Sensor repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.sensor import Sensor


class SensorRepository(ABC):
    @abstractmethod
    async def get_by_id(self, sensor_id: UUID) -> Optional[Sensor]:
        pass

    @abstractmethod
    async def list_by_factory(self, factory_id: UUID) -> List[Sensor]:
        pass

    @abstractmethod
    async def save(self, sensor: Sensor) -> Sensor:
        pass

    @abstractmethod
    async def delete(self, sensor_id: UUID) -> bool:
        pass
