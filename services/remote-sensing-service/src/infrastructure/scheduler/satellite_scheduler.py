"""APScheduler-based satellite data fetch scheduler.

Runs periodic jobs to fetch satellite data from Copernicus CAMS,
NASA MODIS, and Sentinel-5P TROPOMI.  Each job uses a CronTrigger
parsed from the service configuration.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.satellite_source import SatelliteSource
from ..external.copernicus_cams_client import CopernicusCAMSClient
from ..external.nasa_earthdata_client import NASAEarthdataClient
from ..external.sentinel_hub_client import SentinelHubClient

logger = logging.getLogger(__name__)


def _parse_cron(expression: str) -> CronTrigger:
    """Parse a standard 5-field cron expression into an APScheduler CronTrigger."""
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5-field cron expression, got: {expression!r}")
    minute, hour, day, month, day_of_week = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


class SatelliteScheduler:
    """Manages periodic satellite data fetch jobs."""

    def __init__(
        self,
        satellite_service,  # SatelliteDataService (avoid circular import)
    ):
        from ...config import settings

        self.satellite_service = satellite_service
        self.settings = settings
        self.scheduler = AsyncIOScheduler()

        # Build the default city bounding box from config.
        self.city_bbox = GeoPolygon(
            north=settings.CITY_BBOX_NORTH,
            south=settings.CITY_BBOX_SOUTH,
            east=settings.CITY_BBOX_EAST,
            west=settings.CITY_BBOX_WEST,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Register jobs and start the scheduler."""
        if self.settings.CAMS_FETCH_ENABLED:
            self.scheduler.add_job(
                self._fetch_cams,
                trigger=_parse_cron(self.settings.CAMS_FETCH_CRON),
                id="fetch_cams",
                name="Fetch CAMS forecast data",
                replace_existing=True,
            )
            logger.info(
                "CAMS fetch job scheduled: %s", self.settings.CAMS_FETCH_CRON
            )

        if self.settings.MODIS_FETCH_ENABLED:
            self.scheduler.add_job(
                self._fetch_modis,
                trigger=_parse_cron(self.settings.MODIS_FETCH_CRON),
                id="fetch_modis",
                name="Fetch MODIS AOD data",
                replace_existing=True,
            )
            logger.info(
                "MODIS fetch job scheduled: %s", self.settings.MODIS_FETCH_CRON
            )

        if self.settings.TROPOMI_FETCH_ENABLED:
            self.scheduler.add_job(
                self._fetch_tropomi,
                trigger=_parse_cron(self.settings.TROPOMI_FETCH_CRON),
                id="fetch_tropomi",
                name="Fetch TROPOMI trace-gas data",
                replace_existing=True,
            )
            logger.info(
                "TROPOMI fetch job scheduled: %s", self.settings.TROPOMI_FETCH_CRON
            )

        self.scheduler.start()
        logger.info("SatelliteScheduler started")

    def stop(self) -> None:
        """Shut down the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("SatelliteScheduler stopped")

    # ------------------------------------------------------------------
    # Scheduled jobs
    # ------------------------------------------------------------------
    async def _fetch_cams(self) -> None:
        """Fetch CAMS PM2.5 forecast for the configured city bbox."""
        target = date.today()
        logger.info("Scheduler: fetching CAMS data for %s", target)
        try:
            result = await self.satellite_service.fetch_cams_data(
                variable="particulate_matter_2.5um",
                bbox=self.city_bbox,
                target_date=target,
            )
            logger.info("Scheduler: CAMS fetch complete — id=%s", result.id)
        except Exception:
            logger.exception("Scheduler: CAMS fetch failed")

    async def _fetch_modis(self) -> None:
        """Fetch MODIS AOD for the configured city bbox (yesterday)."""
        target = date.today() - timedelta(days=1)
        logger.info("Scheduler: fetching MODIS AOD for %s", target)
        try:
            result = await self.satellite_service.fetch_modis_aod(
                bbox=self.city_bbox,
                target_date=target,
                use_terra=True,
            )
            if result:
                logger.info("Scheduler: MODIS fetch complete — id=%s", result.id)
            else:
                logger.warning("Scheduler: no MODIS data available for %s", target)
        except Exception:
            logger.exception("Scheduler: MODIS fetch failed")

    async def _fetch_tropomi(self) -> None:
        """Fetch TROPOMI NO₂ data for the configured city bbox (yesterday)."""
        target = date.today() - timedelta(days=1)
        logger.info("Scheduler: fetching TROPOMI NO2 for %s", target)
        try:
            result = await self.satellite_service.fetch_tropomi(
                pollutant="NO2",
                bbox=self.city_bbox,
                target_date=target,
            )
            if result:
                logger.info("Scheduler: TROPOMI fetch complete — id=%s", result.id)
            else:
                logger.warning("Scheduler: no TROPOMI data available for %s", target)
        except Exception:
            logger.exception("Scheduler: TROPOMI fetch failed")

    # ------------------------------------------------------------------
    # Manual trigger
    # ------------------------------------------------------------------
    async def trigger_manual_fetch(
        self,
        source: SatelliteSource,
        target_date: Optional[date] = None,
    ) -> dict:
        """Trigger an on-demand fetch for a specific satellite source.

        Returns a dict with ``status`` and ``data`` keys.
        """
        target = target_date or date.today()

        if source in (SatelliteSource.CAMS_PM25, SatelliteSource.CAMS_PM10, SatelliteSource.CAMS_FORECAST):
            result = await self.satellite_service.fetch_cams_data(
                variable="particulate_matter_2.5um",
                bbox=self.city_bbox,
                target_date=target,
            )
            return {"status": "ok", "source": source.value, "data_id": str(result.id)}

        if source in (SatelliteSource.MODIS_TERRA, SatelliteSource.MODIS_AQUA):
            use_terra = source == SatelliteSource.MODIS_TERRA
            result = await self.satellite_service.fetch_modis_aod(
                bbox=self.city_bbox,
                target_date=target,
                use_terra=use_terra,
            )
            if result:
                return {"status": "ok", "source": source.value, "data_id": str(result.id)}
            return {"status": "no_data", "source": source.value, "data_id": None}

        if source.value.startswith("tropomi_"):
            pollutant = source.value.replace("tropomi_", "").upper()
            result = await self.satellite_service.fetch_tropomi(
                pollutant=pollutant,
                bbox=self.city_bbox,
                target_date=target,
            )
            if result:
                return {"status": "ok", "source": source.value, "data_id": str(result.id)}
            return {"status": "no_data", "source": source.value, "data_id": None}

        return {"status": "error", "message": f"Unsupported source: {source.value}"}
