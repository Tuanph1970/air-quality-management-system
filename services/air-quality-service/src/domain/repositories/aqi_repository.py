"""AQI repository interface (port).

Defines the persistence contract for Air Quality Index data.
The domain layer depends on this abstraction.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID


class AQIRepository(ABC):
    """Abstract repository for AQI data persistence."""

    @abstractmethod
    async def get_latest(self, latitude: float, longitude: float, radius_km: float) -> Optional[Dict]:
        """Get the latest AQI reading for a location."""

    @abstractmethod
    async def get_historical(
        self,
        latitude: float,
        longitude: float,
        hours: int = 24,
    ) -> List[Dict]:
        """Get historical AQI readings for forecasting."""

    @abstractmethod
    async def get_within_bounds(
        self,
        min_lat: float,
        min_lng: float,
        max_lat: float,
        max_lng: float,
        since: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get AQI readings within a geographic bounding box."""

    @abstractmethod
    async def save_reading(self, reading: Dict) -> Dict:
        """Save an AQI reading."""

    @abstractmethod
    async def get_sensor_readings(
        self,
        sensor_id: str,
        limit: int = 100,
    ) -> List[Dict]:
        """Get readings from a specific sensor."""
