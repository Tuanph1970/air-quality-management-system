"""HTTP client for the Sensor Service.

Used by the remote-sensing service to fetch recent sensor readings
for data fusion and cross-validation workflows.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://sensor-service:8002"
_TIMEOUT = 15.0


class SensorServiceClient:
    """Synchronous-style async HTTP client for the sensor service."""

    def __init__(self, base_url: str = _DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")

    async def get_latest_readings(
        self,
        factory_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Fetch the most recent sensor readings.

        Returns a list of dicts with keys:
        ``sensor_id``, ``factory_id``, ``lat``, ``lon``, ``value``,
        ``pollutant``, ``timestamp``.
        """
        params: Dict = {"limit": limit}
        if factory_id:
            params["factory_id"] = str(factory_id)

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}/readings/latest",
                params=params,
            )

        if resp.status_code != 200:
            logger.warning(
                "Sensor service request failed: status=%d", resp.status_code
            )
            return []

        return resp.json().get("data", [])

    async def get_readings_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        factory_id: Optional[UUID] = None,
    ) -> List[Dict]:
        """Fetch sensor readings within a time range."""
        params: Dict = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }
        if factory_id:
            params["factory_id"] = str(factory_id)

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}/readings",
                params=params,
            )

        if resp.status_code != 200:
            logger.warning(
                "Sensor service request failed: status=%d", resp.status_code
            )
            return []

        return resp.json().get("data", [])

    async def get_sensor(self, sensor_id: UUID) -> Optional[Dict]:
        """Fetch a single sensor's metadata."""
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{self.base_url}/sensors/{sensor_id}",
            )

        if resp.status_code != 200:
            return None

        return resp.json()
