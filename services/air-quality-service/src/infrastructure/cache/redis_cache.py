"""Redis cache implementation for AQI data.

Provides caching for:
- AQI calculations (short TTL)
- Map data (medium TTL)
- Forecasts (longer TTL)

**Infrastructure layer**: This module handles external concerns (Redis).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from ...config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache for AQI service data.

    Implements caching strategies optimized for air quality data
    with different TTLs based on data volatility.
    """

    # Cache key prefixes
    PREFIX_AQI = f"{settings.REDIS_PREFIX}:aqi"
    PREFIX_MAP = f"{settings.REDIS_PREFIX}:map"
    PREFIX_FORECAST = f"{settings.REDIS_PREFIX}:forecast"
    PREFIX_SENSOR = f"{settings.REDIS_PREFIX}:sensor"

    # TTL configuration (seconds)
    TTL_AQI = settings.CACHE_TTL_DEFAULT  # 5 minutes
    TTL_MAP = settings.CACHE_TTL_MAP_DATA  # 10 minutes
    TTL_FORECAST = settings.CACHE_TTL_FORECAST  # 30 minutes
    TTL_SENSOR = 60  # 1 minute for real-time sensor data

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis cache.

        Parameters
        ----------
        redis_url:
            Redis connection URL (uses config if not provided)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._client = None

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Closed Redis connection")

    async def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except:
            return False

    # =====================================================================
    # AQI Cache Operations
    # =====================================================================

    def _make_aqi_key(self, lat: float, lng: float, radius: float) -> str:
        """Generate cache key for AQI data."""
        # Round coordinates for better cache hit rate
        lat_rounded = round(lat, 3)
        lng_rounded = round(lng, 3)
        return f"{self.PREFIX_AQI}:{lat_rounded}:{lng_rounded}:{radius}"

    async def get_aqi(
        self,
        lat: float,
        lng: float,
        radius: float,
    ) -> Optional[Dict]:
        """Get cached AQI data for a location.

        Parameters
        ----------
        lat:
            Latitude
        lng:
            Longitude
        radius:
            Search radius in km

        Returns
        -------
        dict or None
            Cached AQI data or None if not found
        """
        if not self._client:
            return None

        key = self._make_aqi_key(lat, lng, radius)
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Error getting AQI from cache: {e}")
        return None

    async def set_aqi(
        self,
        lat: float,
        lng: float,
        radius: float,
        aqi_data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache AQI data for a location.

        Parameters
        ----------
        lat:
            Latitude
        lng:
            Longitude
        radius:
            Search radius in km
        aqi_data:
            AQI data to cache
        ttl:
            Custom TTL in seconds (uses default if not provided)

        Returns
        -------
        bool
            True if successfully cached
        """
        if not self._client:
            return False

        key = self._make_aqi_key(lat, lng, radius)
        try:
            await self._client.setex(
                key,
                ttl or self.TTL_AQI,
                json.dumps(aqi_data),
            )
            return True
        except Exception as e:
            logger.warning(f"Error setting AQI in cache: {e}")
            return False

    # =====================================================================
    # Map Data Cache Operations
    # =====================================================================

    def _make_map_key(
        self,
        min_lat: float,
        min_lng: float,
        max_lat: float,
        max_lng: float,
        zoom: int,
    ) -> str:
        """Generate cache key for map data."""
        return f"{self.PREFIX_MAP}:{zoom}:{round(min_lat, 2)}:{round(min_lng, 2)}:{round(max_lat, 2)}:{round(max_lng, 2)}"

    async def get_map_data(
        self,
        min_lat: float,
        min_lng: float,
        max_lat: float,
        max_lng: float,
        zoom: int,
    ) -> Optional[List[Dict]]:
        """Get cached map data.

        Parameters
        ----------
        min_lat, min_lng, max_lat, max_lng:
            Map bounding box
        zoom:
            Zoom level

        Returns
        -------
        list or None
            Cached grid cells or None if not found
        """
        if not self._client:
            return None

        key = self._make_map_key(min_lat, min_lng, max_lat, max_lng, zoom)
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Error getting map data from cache: {e}")
        return None

    async def set_map_data(
        self,
        min_lat: float,
        min_lng: float,
        max_lat: float,
        max_lng: float,
        zoom: int,
        grid_cells: List[Dict],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache map grid data.

        Parameters
        ----------
        min_lat, min_lng, max_lat, max_lng:
            Map bounding box
        zoom:
            Zoom level
        grid_cells:
            List of grid cell data
        ttl:
            Custom TTL in seconds

        Returns
        -------
        bool
            True if successfully cached
        """
        if not self._client:
            return False

        key = self._make_map_key(min_lat, min_lng, max_lat, max_lng, zoom)
        try:
            await self._client.setex(
                key,
                ttl or self.TTL_MAP,
                json.dumps(grid_cells),
            )
            return True
        except Exception as e:
            logger.warning(f"Error setting map data in cache: {e}")
            return False

    # =====================================================================
    # Forecast Cache Operations
    # =====================================================================

    def _make_forecast_key(
        self,
        lat: float,
        lng: float,
        hours: int,
    ) -> str:
        """Generate cache key for forecast data."""
        return f"{self.PREFIX_FORECAST}:{round(lat, 3)}:{round(lng, 3)}:{hours}"

    async def get_forecast(
        self,
        lat: float,
        lng: float,
        hours: int,
    ) -> Optional[Dict]:
        """Get cached forecast data.

        Parameters
        ----------
        lat:
            Latitude
        lng:
            Longitude
        hours:
            Forecast duration

        Returns
        -------
        dict or None
            Cached forecast data or None if not found
        """
        if not self._client:
            return None

        key = self._make_forecast_key(lat, lng, hours)
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Error getting forecast from cache: {e}")
        return None

    async def set_forecast(
        self,
        lat: float,
        lng: float,
        hours: int,
        forecast_data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache forecast data.

        Parameters
        ----------
        lat:
            Latitude
        lng:
            Longitude
        hours:
            Forecast duration
        forecast_data:
            Forecast data to cache
        ttl:
            Custom TTL in seconds

        Returns
        -------
        bool
            True if successfully cached
        """
        if not self._client:
            return False

        key = self._make_forecast_key(lat, lng, hours)
        try:
            await self._client.setex(
                key,
                ttl or self.TTL_FORECAST,
                json.dumps(forecast_data),
            )
            return True
        except Exception as e:
            logger.warning(f"Error setting forecast in cache: {e}")
            return False

    # =====================================================================
    # Sensor Data Cache Operations
    # =====================================================================

    def _make_sensor_key(self, sensor_id: str) -> str:
        """Generate cache key for sensor data."""
        return f"{self.PREFIX_SENSOR}:{sensor_id}"

    async def get_sensor_data(self, sensor_id: str) -> Optional[Dict]:
        """Get cached sensor reading.

        Parameters
        ----------
        sensor_id:
            Sensor identifier

        Returns
        -------
        dict or None
            Cached sensor data or None if not found
        """
        if not self._client:
            return None

        key = self._make_sensor_key(sensor_id)
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Error getting sensor data from cache: {e}")
        return None

    async def set_sensor_data(
        self,
        sensor_id: str,
        sensor_data: Dict,
        ttl: int = 60,
    ) -> bool:
        """Cache sensor reading.

        Parameters
        ----------
        sensor_id:
            Sensor identifier
        sensor_data:
            Sensor data to cache
        ttl:
            TTL in seconds (default 60 for real-time data)

        Returns
        -------
        bool
            True if successfully cached
        """
        if not self._client:
            return False

        key = self._make_sensor_key(sensor_id)
        try:
            await self._client.setex(
                key,
                ttl,
                json.dumps(sensor_data),
            )
            return True
        except Exception as e:
            logger.warning(f"Error setting sensor data in cache: {e}")
            return False

    # =====================================================================
    # General Cache Operations
    # =====================================================================

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Parameters
        ----------
        pattern:
            Redis key pattern (e.g., "aqms:aqi:*")

        Returns
        -------
        int
            Number of keys deleted
        """
        if not self._client:
            return 0

        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Error deleting pattern {pattern}: {e}")
            return 0

    async def clear_all(self) -> bool:
        """Clear all cached data with our prefix.

        Returns
        -------
        bool
            True if successfully cleared
        """
        if not self._client:
            return False

        try:
            pattern = f"{settings.REDIS_PREFIX}:*"
            return await self.delete_pattern(pattern)
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
            return False
