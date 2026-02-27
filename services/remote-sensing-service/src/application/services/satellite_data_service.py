"""Application service for satellite data operations.

Orchestrates fetching from external satellite APIs, persistence,
and domain event publication.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Dict, List, Optional

from ...domain.entities.satellite_data import SatelliteData
from ...domain.repositories.satellite_data_repository import SatelliteDataRepository
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.satellite_source import SatelliteSource
from ...infrastructure.external.copernicus_cams_client import CopernicusCAMSClient
from ...infrastructure.external.nasa_earthdata_client import NASAEarthdataClient
from ...infrastructure.external.sentinel_hub_client import SentinelHubClient
from ..dto.satellite_data_dto import SatelliteDataDTO
from shared.messaging.publisher import RabbitMQPublisher
from shared.messaging.config import SATELLITE_EXCHANGE

logger = logging.getLogger(__name__)


class SatelliteDataService:
    """Application service for satellite data operations."""

    def __init__(
        self,
        repository: SatelliteDataRepository,
        cams_client: CopernicusCAMSClient,
        nasa_client: NASAEarthdataClient,
        sentinel_client: SentinelHubClient,
        event_publisher: RabbitMQPublisher,
    ):
        self.repository = repository
        self.cams_client = cams_client
        self.nasa_client = nasa_client
        self.sentinel_client = sentinel_client
        self.event_publisher = event_publisher

    # ------------------------------------------------------------------
    # Fetch operations
    # ------------------------------------------------------------------
    async def fetch_cams_data(
        self,
        variable: str,
        bbox: GeoPolygon,
        target_date: date,
    ) -> SatelliteDataDTO:
        """Fetch CAMS forecast/reanalysis data, persist, and publish events."""
        logger.info("Fetching CAMS data: variable=%s date=%s", variable, target_date)

        data = await self.cams_client.get_forecast(variable, bbox, target_date)
        saved = await self.repository.save(data)

        for event in saved.collect_events():
            await self.event_publisher.publish(event, SATELLITE_EXCHANGE)

        return SatelliteDataDTO.from_entity(saved)

    async def fetch_modis_aod(
        self,
        bbox: GeoPolygon,
        target_date: date,
        use_terra: bool = True,
    ) -> Optional[SatelliteDataDTO]:
        """Fetch MODIS AOD data, persist, and publish events."""
        product = "MOD04_L2" if use_terra else "MYD04_L2"
        logger.info("Fetching MODIS AOD: product=%s date=%s", product, target_date)

        data = await self.nasa_client.get_modis_aod(product, bbox, target_date)
        if not data:
            return None

        saved = await self.repository.save(data)

        for event in saved.collect_events():
            await self.event_publisher.publish(event, SATELLITE_EXCHANGE)

        return SatelliteDataDTO.from_entity(saved)

    async def fetch_tropomi(
        self,
        pollutant: str,
        bbox: GeoPolygon,
        target_date: date,
    ) -> Optional[SatelliteDataDTO]:
        """Fetch TROPOMI trace-gas data, persist, and publish events."""
        logger.info("Fetching TROPOMI: pollutant=%s date=%s", pollutant, target_date)

        data = await self.sentinel_client.get_tropomi_data(
            pollutant, bbox, target_date
        )
        if not data:
            return None

        saved = await self.repository.save(data)

        for event in saved.collect_events():
            await self.event_publisher.publish(event, SATELLITE_EXCHANGE)

        return SatelliteDataDTO.from_entity(saved)

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------
    async def get_by_id(self, data_id) -> Optional[SatelliteDataDTO]:
        """Get satellite data by ID."""
        data = await self.repository.get_by_id(data_id)
        return SatelliteDataDTO.from_entity(data) if data else None

    async def get_latest(
        self, source: SatelliteSource, data_type: str
    ) -> Optional[SatelliteDataDTO]:
        """Get latest satellite data for a given source and type."""
        data = await self.repository.get_latest(source, data_type)
        return SatelliteDataDTO.from_entity(data) if data else None

    async def get_data_for_location(
        self, lat: float, lon: float
    ) -> Dict[str, Dict]:
        """Get all available satellite data values for a specific location.

        Returns a dict keyed by source name with value, observation time,
        and quality flag.
        """
        result: Dict[str, Dict] = {}

        for source in SatelliteSource:
            # Derive data_type from the source enum value.
            parts = source.value.split("_")
            data_type = parts[-1].upper() if len(parts) > 1 else source.value.upper()

            data = await self.repository.get_latest(source, data_type)
            if data is None:
                continue

            value = data.get_value_at(lat, lon)
            if value is not None:
                result[source.value] = {
                    "value": value,
                    "observation_time": data.observation_time.isoformat(),
                    "quality": data.quality_flag.value,
                }

        return result

    async def get_by_time_range(
        self,
        source: SatelliteSource,
        start_time: datetime,
        end_time: datetime,
        bbox: Optional[GeoPolygon] = None,
    ) -> List[SatelliteDataDTO]:
        """Get satellite data within a time range."""
        data_list = await self.repository.get_by_time_range(
            source, start_time, end_time, bbox
        )
        return [SatelliteDataDTO.from_entity(d) for d in data_list]

    async def cleanup_old_data(self, days: int = 90) -> int:
        """Remove satellite data older than the given number of days."""
        deleted = await self.repository.delete_older_than(days)
        logger.info("Cleaned up %d satellite data records older than %d days", deleted, days)
        return deleted
