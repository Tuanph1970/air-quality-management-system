"""Fused data repository interface (port)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..entities.fused_data import FusedData
from ..value_objects.geo_polygon import GeoPolygon


class FusedDataRepository(ABC):
    """Repository interface for fused data persistence."""

    @abstractmethod
    async def get_by_id(self, fusion_id: UUID) -> Optional[FusedData]:
        pass

    @abstractmethod
    async def get_latest(self, pollutant: str = "") -> Optional[FusedData]:
        pass

    @abstractmethod
    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        bbox: Optional[GeoPolygon] = None,
    ) -> List[FusedData]:
        pass

    @abstractmethod
    async def save(self, fused_data: FusedData) -> FusedData:
        pass

    @abstractmethod
    async def delete_older_than(self, days: int) -> int:
        pass
