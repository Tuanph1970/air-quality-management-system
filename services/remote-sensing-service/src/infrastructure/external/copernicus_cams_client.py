"""Client for Copernicus Atmosphere Monitoring Service (CAMS).

Fetches air quality forecast and reanalysis data via the CDS API,
then parses the resulting NetCDF files into domain entities.
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import date, datetime
from typing import Dict, List, Optional

import cdsapi

from ...domain.entities.satellite_data import SatelliteData
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.quality_flag import QualityFlag
from ...domain.value_objects.satellite_source import SatelliteSource
from ..parsers.netcdf_parser import NetCDFParser

logger = logging.getLogger(__name__)

# Map short variable names → CAMS dataset variable identifiers.
_VARIABLE_MAP: Dict[str, str] = {
    "pm2p5": "particulate_matter_2.5um",
    "pm10": "particulate_matter_10um",
    "no2": "nitrogen_dioxide",
    "o3": "ozone",
    "so2": "sulphur_dioxide",
    "co": "carbon_monoxide",
}

# Map variable prefix → SatelliteSource.
_SOURCE_MAP: Dict[str, SatelliteSource] = {
    "pm2p5": SatelliteSource.CAMS_PM25,
    "pm10": SatelliteSource.CAMS_PM10,
}


class CopernicusCAMSClient:
    """Copernicus CAMS data client.

    Uses the ``cdsapi`` library for synchronous data retrieval (wrapped
    in async where needed) and the NetCDFParser for file parsing.
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://ads.atmosphere.copernicus.eu/api/v2",
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.parser = NetCDFParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_forecast(
        self,
        variable: str,
        bbox: GeoPolygon,
        target_date: date,
        leadtime_hours: Optional[List[int]] = None,
    ) -> SatelliteData:
        """Fetch CAMS global air quality forecast.

        Parameters
        ----------
        variable:
            Short variable name: ``pm2p5``, ``pm10``, ``no2``, ``o3``,
            ``so2``, ``co``.
        bbox:
            Geographic bounding box for the request.
        target_date:
            Forecast base date.
        leadtime_hours:
            Lead-time hours to retrieve (default ``[0, 6, 12, 18, 24]``).
        """
        leadtime_hours = leadtime_hours or [0, 6, 12, 18, 24]

        cds_variable = _VARIABLE_MAP.get(variable, variable)

        tmp_path = self._make_tmp_path()
        try:
            self._retrieve(
                dataset="cams-global-atmospheric-composition-forecasts",
                request={
                    "variable": cds_variable,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "time": "00:00",
                    "leadtime_hour": [str(h) for h in leadtime_hours],
                    "type": "forecast",
                    "area": [bbox.north, bbox.west, bbox.south, bbox.east],
                    "format": "netcdf",
                },
                target=tmp_path,
            )

            grid_cells = self.parser.parse_cams(tmp_path, variable)

            source = _SOURCE_MAP.get(variable, SatelliteSource.CAMS_FORECAST)

            logger.info(
                "CAMS forecast retrieved: variable=%s date=%s cells=%d",
                variable,
                target_date,
                len(grid_cells),
            )

            return SatelliteData.create(
                source=source,
                data_type=variable.upper(),
                observation_time=datetime.combine(
                    target_date, datetime.min.time()
                ),
                bbox=bbox,
                grid_cells=grid_cells,
                quality_flag=QualityFlag.GOOD,
                metadata={"leadtime_hours": leadtime_hours},
            )
        finally:
            self._cleanup(tmp_path)

    async def get_reanalysis(
        self,
        variable: str,
        bbox: GeoPolygon,
        start_date: date,
        end_date: date,
    ) -> List[SatelliteData]:
        """Fetch CAMS reanalysis (historical) data.

        Downloads a single NetCDF covering the requested date range,
        then returns one ``SatelliteData`` per day contained in the file.
        """
        cds_variable = _VARIABLE_MAP.get(variable, variable)

        tmp_path = self._make_tmp_path()
        try:
            self._retrieve(
                dataset="cams-global-reanalysis-eac4",
                request={
                    "variable": cds_variable,
                    "date": f"{start_date:%Y-%m-%d}/{end_date:%Y-%m-%d}",
                    "time": ["00:00", "06:00", "12:00", "18:00"],
                    "area": [bbox.north, bbox.west, bbox.south, bbox.east],
                    "format": "netcdf",
                },
                target=tmp_path,
            )

            grid_cells = self.parser.parse_cams(tmp_path, variable)
            source = _SOURCE_MAP.get(variable, SatelliteSource.CAMS_FORECAST)

            result = SatelliteData.create(
                source=source,
                data_type=variable.upper(),
                observation_time=datetime.combine(
                    start_date, datetime.min.time()
                ),
                bbox=bbox,
                grid_cells=grid_cells,
                quality_flag=QualityFlag.GOOD,
                metadata={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "type": "reanalysis",
                },
            )

            logger.info(
                "CAMS reanalysis retrieved: variable=%s range=%s–%s cells=%d",
                variable,
                start_date,
                end_date,
                len(grid_cells),
            )
            return [result]
        finally:
            self._cleanup(tmp_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _retrieve(
        self, dataset: str, request: dict, target: str
    ) -> None:
        """Synchronous CDS API retrieve (blocking)."""
        client = cdsapi.Client(url=self.api_url, key=self.api_key)
        client.retrieve(dataset, request, target)

    @staticmethod
    def _make_tmp_path() -> str:
        fd, path = tempfile.mkstemp(suffix=".nc")
        os.close(fd)
        return path

    @staticmethod
    def _cleanup(path: str) -> None:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            logger.warning("Failed to clean up temp file: %s", path)
