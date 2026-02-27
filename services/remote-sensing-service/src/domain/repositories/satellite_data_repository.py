"""Satellite data repository interface (port)."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..entities.satellite_data import SatelliteData
from ..value_objects.satellite_source import SatelliteSource
from ..value_objects.geo_polygon import GeoPolygon


class SatelliteDataRepository(ABC):
    """Repository interface for satellite data persistence."""

    @abstractmethod
    async def get_by_id(self, data_id: UUID) -> Optional[SatelliteData]:
        pass

    @abstractmethod
    async def get_latest(
        self, source: SatelliteSource, data_type: str
    ) -> Optional[SatelliteData]:
        pass

    @abstractmethod
    async def get_by_time_range(
        self,
        source: SatelliteSource,
        start_time: datetime,
        end_time: datetime,
        bbox: Optional[GeoPolygon] = None,
    ) -> List[SatelliteData]:
        pass

    @abstractmethod
    async def save(self, data: SatelliteData) -> SatelliteData:
        pass

    @abstractmethod
    async def delete_older_than(self, days: int) -> int:
        pass
