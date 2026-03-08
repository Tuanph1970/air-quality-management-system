"""GFS (Global Forecast System) data downloader.

Downloads boundary condition data from NOAA's NOMADS server for WRF preprocessing.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import httpx

from ...domain.value_objects.wrf_config import WRFConfig
from ..config import settings

logger = logging.getLogger(__name__)


class GFSDataDownloader:
    """Downloads GFS forecast data for WRF boundary conditions."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or settings.GFS_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = settings.GFS_SOURCE_URL
        self.timeout = settings.GFS_DOWNLOAD_TIMEOUT

    async def download(
        self, config: WRFConfig, simulation_id: UUID
    ) -> str:
        """
        Download GFS data for the specified simulation.

        Args:
            config: WRF configuration with domain and timing
            simulation_id: ID of the simulation

        Returns:
            Path to downloaded GFS data directory
        """
        simulation_dir = self.data_dir / str(simulation_id)
        simulation_dir.mkdir(parents=True, exist_ok=True)

        # Determine GFS forecast time needed
        forecast_hours = config.simulation_hours + 6  # Buffer for boundary conditions
        forecast_hours = min(forecast_hours, settings.GFS_MAX_FORECAST_HOURS)

        # Get latest available GFS run
        gfs_date = self._get_latest_gfs_date()

        logger.info(
            f"Downloading GFS data for simulation {simulation_id}: "
            f"date={gfs_date}, forecast_hours={forecast_hours}"
        )

        # Download GRIB2 files
        grib_files = await self._download_grib_files(
            gfs_date, forecast_hours, simulation_dir
        )

        logger.info(f"Downloaded {len(grib_files)} GFS GRIB files")

        return str(simulation_dir)

    def _get_latest_gfs_date(self) -> datetime:
        """Get the latest available GFS forecast date."""
        # In production, this would query NOMADS for available dates
        # For now, use current time rounded to nearest 6-hour cycle
        now = datetime.utcnow()
        hour = (now.hour // 6) * 6
        gfs_date = now.replace(hour=hour, minute=0, second=0, microsecond=0)

        # Subtract 3 hours to ensure data is available
        gfs_date -= timedelta(hours=3)

        return gfs_date

    async def _download_grib_files(
        self,
        start_date: datetime,
        forecast_hours: int,
        output_dir: Path,
    ) -> List[Path]:
        """Download required GFS GRIB2 files."""
        grib_files = []

        # GFS provides forecast files at intervals
        # 0-240h: every hour (we'll sample every 3 hours for efficiency)
        interval = 3

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = []
            for hour in range(0, min(forecast_hours, 240), interval):
                grib_url = self._build_grib_url(start_date, hour)
                output_path = output_dir / f"gfs_f{hour:03d}.grib2"

                if not output_path.exists():
                    tasks.append(self._download_file(client, grib_url, output_path))

                grib_files.append(output_path)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        return grib_files

    def _build_grib_url(self, date: datetime, forecast_hour: int) -> str:
        """Build URL for GFS GRIB2 file."""
        date_str = date.strftime("%Y%m%d/%H")
        return (
            f"{self.base_url}/gfs.{date_str}/atmos/gfs.t{date.strftime('%H')}z."
            f"pgrb2.0p25.f{forecast_hour:03d}"
        )

    async def _download_file(
        self, client: httpx.AsyncClient, url: str, output_path: Path
    ) -> None:
        """Download a single file with retry logic."""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                logger.debug(f"Downloading {url}")

                async with client.stream("GET", url) as response:
                    if response.status_code == 200:
                        with open(output_path, "wb") as f:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                f.write(chunk)
                        logger.debug(f"Downloaded {output_path}")
                        return
                    else:
                        logger.warning(
                            f"GFS download failed: {response.status_code} for {url}"
                        )

            except httpx.TimeoutException:
                logger.warning(f"Timeout downloading {url}, attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"Error downloading {url}: {e}, attempt {attempt + 1}")

            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        logger.error(f"Failed to download {url} after {max_retries} attempts")

    async def download_sample_data(self, simulation_id: UUID) -> str:
        """
        Download sample/dummy GFS data for testing without WRF.

        This creates placeholder files for development/testing.
        """
        simulation_dir = self.data_dir / str(simulation_id)
        simulation_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy GRIB files
        for hour in range(0, 48, 3):
            grib_path = simulation_dir / f"gfs_f{hour:03d}.grib2"
            grib_path.write_text(f"DUMMY GFS DATA FOR HOUR {hour}")

        logger.info(f"Created sample GFS data in {simulation_dir}")
        return str(simulation_dir)
