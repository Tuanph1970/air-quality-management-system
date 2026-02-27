"""Client for NASA Earthdata — MODIS Aerosol Optical Depth data.

Uses the LAADS DAAC API to search and download MODIS L2 products
(MOD04_L2 for Terra, MYD04_L2 for Aqua).
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import date, datetime
from typing import Optional

import httpx

from ...domain.entities.satellite_data import SatelliteData
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.quality_flag import QualityFlag
from ...domain.value_objects.satellite_source import SatelliteSource
from ..parsers.netcdf_parser import NetCDFParser

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://ladsweb.modaps.eosdis.nasa.gov/api/v2"
_DOWNLOAD_TIMEOUT = 120.0  # seconds


class NASAEarthdataClient:
    """NASA Earthdata (LAADS DAAC) client for MODIS AOD data."""

    def __init__(
        self,
        token: str,
        base_url: str = _DEFAULT_BASE_URL,
    ):
        self.token = token
        self.base_url = base_url
        self.parser = NetCDFParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_modis_aod(
        self,
        product: str,
        bbox: GeoPolygon,
        target_date: date,
    ) -> Optional[SatelliteData]:
        """Fetch MODIS Aerosol Optical Depth data.

        Parameters
        ----------
        product:
            MODIS product identifier — ``MOD04_L2`` (Terra) or
            ``MYD04_L2`` (Aqua).
        bbox:
            Geographic bounding box.
        target_date:
            Date to retrieve.

        Returns ``None`` if no matching file is available.
        """
        headers = {"Authorization": f"Bearer {self.token}"}

        file_info = await self._search_files(
            product, bbox, target_date, headers
        )
        if file_info is None:
            logger.info(
                "No MODIS files found for %s on %s", product, target_date
            )
            return None

        tmp_path = self._make_tmp_path(suffix=".hdf")
        try:
            await self._download_file(
                file_info["downloadsLink"], headers, tmp_path
            )

            grid_cells = self.parser.parse_modis_aod(tmp_path)

            source = (
                SatelliteSource.MODIS_TERRA
                if "MOD" in product
                else SatelliteSource.MODIS_AQUA
            )

            logger.info(
                "MODIS AOD retrieved: product=%s date=%s cells=%d",
                product,
                target_date,
                len(grid_cells),
            )

            return SatelliteData.create(
                source=source,
                data_type="AOD",
                observation_time=datetime.combine(
                    target_date, datetime.min.time()
                ),
                bbox=bbox,
                grid_cells=grid_cells,
                quality_flag=QualityFlag.GOOD,
                metadata={"product": product},
            )
        finally:
            self._cleanup(tmp_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _search_files(
        self,
        product: str,
        bbox: GeoPolygon,
        target_date: date,
        headers: dict,
    ) -> Optional[dict]:
        """Search LAADS DAAC for available granules."""
        params = {
            "products": product,
            "temporalRange": target_date.strftime("%Y-%m-%d"),
            "bbox": (
                f"{bbox.west},{bbox.south},{bbox.east},{bbox.north}"
            ),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/content/details",
                headers=headers,
                params=params,
            )

        if resp.status_code != 200:
            logger.warning(
                "LAADS search failed: status=%d body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        data = resp.json()
        content = data.get("content")
        if not content:
            return None

        return content[0]

    async def _download_file(
        self, url: str, headers: dict, dest: str
    ) -> None:
        """Download a file from LAADS DAAC."""
        async with httpx.AsyncClient(timeout=_DOWNLOAD_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        with open(dest, "wb") as fh:
            fh.write(resp.content)

    @staticmethod
    def _make_tmp_path(suffix: str = ".nc") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path

    @staticmethod
    def _cleanup(path: str) -> None:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            logger.warning("Failed to clean up temp file: %s", path)
