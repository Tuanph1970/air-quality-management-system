"""Google Maps Air Quality API client.

Provides integration with Google's Air Quality API for:
- Current air quality conditions
- Air quality heatmap tiles
- Historical data

**Infrastructure layer**: This module handles external API concerns.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from ...config import settings

logger = logging.getLogger(__name__)


@dataclass
class AirQualityCondition:
    """Air quality condition data from Google API."""

    latitude: float
    longitude: float
    aqi: int
    pollutants: Dict[str, float]
    timestamp: str
    source: str = "google"


class GoogleMapsClient:
    """Client for Google Maps Air Quality API.

    Provides methods to fetch air quality data from Google's API.
    Falls back gracefully if API key is not configured.
    """

    BASE_URL = "https://airquality.googleapis.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """Initialize Google Maps client.

        Parameters
        ----------
        api_key:
            Google Maps API key (uses config if not provided)
        timeout:
            Request timeout in seconds
        """
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"X-Goog-Api-Key": self.api_key} if self.api_key else {},
        )
        if self.api_key:
            logger.info("Google Maps client initialized")
        else:
            logger.warning("Google Maps API key not configured")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def get_current_conditions(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[AirQualityCondition]:
        """Get current air quality conditions for a location.

        Parameters
        ----------
        latitude:
            Location latitude
        longitude:
            Location longitude

        Returns
        -------
        AirQualityCondition or None
            Current conditions or None if unavailable
        """
        if not self.api_key:
            logger.debug("Google Maps API key not configured, skipping")
            return None

        if not self._client:
            await self.connect()

        try:
            url = f"{self.BASE_URL}/currentConditions"
            params = {
                "location": f"{latitude},{longitude}",
                "pageSize": 1,
            }

            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("conditions"):
                return None

            condition = data["conditions"][0]
            pollutants = self._parse_pollutants(condition.get("pollutantConcentrations", {}))

            return AirQualityCondition(
                latitude=latitude,
                longitude=longitude,
                aqi=condition.get("overallAQI", 0),
                pollutants=pollutants,
                timestamp=condition.get("dateTime", ""),
                source="google",
            )

        except httpx.TimeoutException:
            logger.warning("Google Maps API request timed out")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"Google Maps API error: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching Google Maps data: {e}")
            return None

    async def get_heatmap_tile(
        self,
        zoom: int,
        x: int,
        y: int,
    ) -> Optional[bytes]:
        """Get air quality heatmap tile.

        Parameters
        ----------
        zoom:
            Zoom level
        x:
            Tile X coordinate
        y:
            Tile Y coordinate

        Returns
        -------
        bytes or None
            Tile image data or None if unavailable
        """
        if not self.api_key:
            return None

        if not self._client:
            await self.connect()

        try:
            url = f"https://tile.googleapis.com/v1/airQuality/tiles/{zoom}/{x}/{y}"
            params = {"key": self.api_key}

            response = await self._client.get(url, params=params)
            response.raise_for_status()

            return response.content

        except Exception as e:
            logger.warning(f"Error fetching heatmap tile: {e}")
            return None

    async def get_stations_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
    ) -> List[Dict]:
        """Get air quality monitoring stations near a location.

        Parameters
        ----------
        latitude:
            Location latitude
        longitude:
            Location longitude
        radius_km:
            Search radius in kilometers

        Returns
        -------
        list
            List of station data
        """
        if not self.api_key:
            return []

        if not self._client:
            await self.connect()

        try:
            url = f"{self.BASE_URL}/stations:search"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": f"{radius_km}km",
            }

            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get("stations", [])

        except Exception as e:
            logger.warning(f"Error fetching stations: {e}")
            return []

    def _parse_pollutants(self, concentrations: Dict) -> Dict[str, float]:
        """Parse pollutant concentrations from Google API response.

        Parameters
        ----------
        concentrations:
            Raw concentration data from API

        Returns
        -------
        dict
            Parsed pollutant concentrations in standard units
        """
        pollutants = {}

        # Google API returns concentrations in μg/m³
        mapping = {
            "pm25Concentration": "pm25",
            "pm10Concentration": "pm10",
            "coConcentration": "co",
            "no2Concentration": "no2",
            "so2Concentration": "so2",
            "o3Concentration": "o3",
        }

        for api_key, standard_key in mapping.items():
            if api_key in concentrations:
                value = concentrations[api_key]
                if value is not None:
                    pollutants[standard_key] = float(value)

        return pollutants

    def is_configured(self) -> bool:
        """Check if Google Maps API is configured.

        Returns
        -------
        bool
            True if API key is set
        """
        return bool(self.api_key)


# Fallback client for when Google API is not available
class FallbackAirQualityClient:
    """Fallback air quality client using local calculations.

    Used when Google Maps API is not configured or unavailable.
    """

    async def get_current_conditions(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[AirQualityCondition]:
        """Get current conditions (always returns None).

        This is a no-op fallback implementation.
        """
        return None

    async def get_heatmap_tile(
        self,
        zoom: int,
        x: int,
        y: int,
    ) -> Optional[bytes]:
        """Get heatmap tile (always returns None).

        This is a no-op fallback implementation.
        """
        return None
