"""Client for Sentinel Hub — Sentinel-5P TROPOMI data.

Retrieves trace-gas column data (NO2, SO2, O3, CO) from the
Sentinel Hub Processing API via OAuth2 client-credentials flow.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import httpx

from ...domain.entities.satellite_data import SatelliteData
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.grid_cell import GridCell
from ...domain.value_objects.quality_flag import QualityFlag
from ...domain.value_objects.satellite_source import SatelliteSource

logger = logging.getLogger(__name__)

_AUTH_URL = "https://services.sentinel-hub.com/oauth/token"
_API_URL = "https://creodias.sentinel-hub.com/api/v1"

_SOURCE_MAP: Dict[str, SatelliteSource] = {
    "NO2": SatelliteSource.TROPOMI_NO2,
    "SO2": SatelliteSource.TROPOMI_SO2,
    "O3": SatelliteSource.TROPOMI_O3,
    "CO": SatelliteSource.TROPOMI_CO,
}


class SentinelHubClient:
    """Sentinel Hub (Sentinel-5P TROPOMI) data client."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_tropomi_data(
        self,
        product: str,
        bbox: GeoPolygon,
        target_date: date,
    ) -> Optional[SatelliteData]:
        """Fetch Sentinel-5P TROPOMI data for a single product.

        Parameters
        ----------
        product:
            Pollutant code — ``NO2``, ``SO2``, ``O3``, or ``CO``.
        bbox:
            Geographic bounding box.
        target_date:
            Target observation date.
        """
        if self._token is None:
            await self._authenticate()

        headers = {"Authorization": f"Bearer {self._token}"}

        request_body = self._build_request(product, bbox, target_date)

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_API_URL}/process",
                headers=headers,
                json=request_body,
            )

        if resp.status_code == 401:
            # Token may have expired — re-authenticate and retry once.
            await self._authenticate()
            headers = {"Authorization": f"Bearer {self._token}"}
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{_API_URL}/process",
                    headers=headers,
                    json=request_body,
                )

        if resp.status_code != 200:
            logger.warning(
                "Sentinel Hub request failed: status=%d body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        data = resp.json()
        grid_cells = self._parse_response(data)
        source = _SOURCE_MAP.get(product, SatelliteSource.TROPOMI_NO2)

        logger.info(
            "TROPOMI data retrieved: product=%s date=%s cells=%d",
            product,
            target_date,
            len(grid_cells),
        )

        return SatelliteData.create(
            source=source,
            data_type=product,
            observation_time=datetime.combine(
                target_date, datetime.min.time()
            ),
            bbox=bbox,
            grid_cells=grid_cells,
            quality_flag=QualityFlag.GOOD,
            metadata={"product": f"S5P_L2_{product}"},
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    async def _authenticate(self) -> str:
        """Obtain an OAuth2 access token via client-credentials grant."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            resp.raise_for_status()
            result = resp.json()

        self._token = result["access_token"]
        logger.info("Sentinel Hub OAuth2 token acquired")
        return self._token

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_request(
        product: str, bbox: GeoPolygon, target_date: date
    ) -> dict:
        """Build a Sentinel Hub Processing API request body."""
        return {
            "input": {
                "bounds": {
                    "bbox": [bbox.west, bbox.south, bbox.east, bbox.north]
                },
                "data": [
                    {
                        "type": f"S5P_L2_{product}",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{target_date}T00:00:00Z",
                                "to": f"{target_date}T23:59:59Z",
                            }
                        },
                    }
                ],
            },
            "output": {
                "responses": [
                    {"format": {"type": "application/json"}}
                ]
            },
        }

    @staticmethod
    def _parse_response(data: dict) -> List[GridCell]:
        """Parse Sentinel Hub JSON response into GridCell list.

        The exact response schema depends on the evalscript configured
        on the Sentinel Hub side.  This implementation handles a flat
        array of ``{lat, lon, value}`` objects as well as an empty /
        missing ``data`` key.
        """
        grid_cells: List[GridCell] = []

        records = data.get("data", [])
        if not isinstance(records, list):
            return grid_cells

        for rec in records:
            try:
                grid_cells.append(
                    GridCell(
                        lat=float(rec["lat"]),
                        lon=float(rec["lon"]),
                        value=float(rec["value"]),
                        uncertainty=float(rec.get("uncertainty", 0.0)),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue

        return grid_cells
