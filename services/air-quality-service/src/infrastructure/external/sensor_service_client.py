"""Sensor Service API client.

Provides integration with the Sensor Service for:
- Getting recent sensor readings
- Getting historical data
- Getting sensor metadata

**Infrastructure layer**: This module handles inter-service communication.
"""
from __future__ import annotations

import logging
import typing
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Sensor reading data from Sensor Service."""

    sensor_id: str
    factory_id: str
    latitude: float
    longitude: float
    pm25: float
    pm10: float
    co: float
    no2: float
    so2: float
    o3: float
    aqi: int
    timestamp: datetime
    status: str = "ACTIVE"


class SensorServiceClient:
    """Client for Sensor Service API.

    Provides methods to fetch sensor data from the Sensor Service.
    Uses environment-based service discovery.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """Initialize Sensor Service client.

        Parameters
        ----------
        base_url:
            Sensor Service base URL (default: http://sensor-service:8002)
        timeout:
            Request timeout in seconds
        """
        self.base_url = base_url or "http://sensor-service:8002"
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            base_url=self.base_url,
        )
        logger.info("Sensor Service client initialized (base_url=%s)", self.base_url)

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def get_sensor_readings(
        self,
        sensor_id: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> List[SensorReading]:
        """Get historical readings for a sensor.

        Parameters
        ----------
        sensor_id:
            Sensor identifier
        start:
            Start timestamp
        end:
            End timestamp
        limit:
            Maximum number of readings to return

        Returns
        -------
        list
            List of sensor readings
        """
        if not self._client:
            await self.connect()

        try:
            params = {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "limit": limit,
            }
            response = await self._client.get(
                f"/api/v1/sensors/{sensor_id}/readings",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            return [self._parse_reading(r) for r in data.get("data", [])]

        except httpx.TimeoutException:
            logger.warning("Sensor Service request timed out")
            return []
        except httpx.HTTPStatusError as e:
            logger.warning(f"Sensor Service error: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching sensor readings: {e}")
            return []

    async def get_recent_readings(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 50,
    ) -> List[SensorReading]:
        """Get recent readings from sensors near a location.

        Parameters
        ----------
        latitude:
            Location latitude
        longitude:
            Location longitude
        radius_km:
            Search radius in kilometers
        limit:
            Maximum readings to return

        Returns
        -------
        list
            List of recent sensor readings
        """
        if not self._client:
            await self.connect()

        try:
            params = {
                "lat": latitude,
                "lng": longitude,
                "radius_km": radius_km,
                "limit": limit,
            }
            response = await self._client.get(
                "/api/v1/readings/recent/nearby",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            return [self._parse_reading(r) for r in data.get("data", [])]

        except httpx.TimeoutException:
            logger.warning("Sensor Service request timed out")
            return []
        except httpx.HTTPStatusError as e:
            logger.warning(f"Sensor Service error: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching nearby readings: {e}")
            return []

    async def get_sensor_info(self, sensor_id: str) -> Optional[Dict]:
        """Get sensor metadata.

        Parameters
        ----------
        sensor_id:
            Sensor identifier

        Returns
        -------
        dict or None
            Sensor information or None if not found
        """
        if not self._client:
            await self.connect()

        try:
            response = await self._client.get(f"/api/v1/sensors/{sensor_id}")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.warning(f"Error fetching sensor info: {e}")
            return None

    async def get_all_active_sensors(self) -> List[Dict]:
        """Get all active sensors.

        Returns
        -------
        list
            List of active sensor information
        """
        if not self._client:
            await self.connect()

        try:
            response = await self._client.get("/api/v1/sensors?status=ACTIVE")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])

        except Exception as e:
            logger.warning(f"Error fetching active sensors: {e}")
            return []

    def _parse_reading(self, data: Dict) -> SensorReading:
        """Parse sensor reading from API response."""
        return SensorReading(
            sensor_id=data.get("sensor_id", ""),
            factory_id=data.get("factory_id", ""),
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            pm25=data.get("pm25", 0.0),
            pm10=data.get("pm10", 0.0),
            co=data.get("co", 0.0),
            no2=data.get("no2", 0.0),
            so2=data.get("so2", 0.0),
            o3=data.get("o3", 0.0),
            aqi=data.get("aqi", 0),
            timestamp=datetime.fromisoformat(data.get("timestamp", "")),
            status=data.get("status", "ACTIVE"),
        )

    def is_available(self) -> bool:
        """Check if Sensor Service is available."""
        return self._client is not None


# =============================================================================
# Dependency Injection
# =============================================================================


def get_sensor_service_client() -> typing.AsyncGenerator[SensorServiceClient, None]:
    """FastAPI dependency for Sensor Service client.

    Usage::

        @router.get("/history")
        async def get_history(
            sensor_client: SensorServiceClient = Depends(get_sensor_service_client)
        ):
            ...
    """
    import os

    async def _generate():
        # Get base URL from environment or use default
        base_url = os.getenv(
            "SENSOR_SERVICE_URL",
            "http://sensor-service:8002",
        )

        client = SensorServiceClient(base_url=base_url)
        await client.connect()
        try:
            yield client
        finally:
            await client.close()

    return _generate()
