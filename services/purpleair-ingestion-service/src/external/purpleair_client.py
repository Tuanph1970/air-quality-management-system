"""PurpleAir API client."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class PurpleAirAPIClient:
    """Client for PurpleAir Cloud API.
    
    PurpleAir API documentation:
    https://api.purpleair.com/
    
    Supports:
    - Fetching sensor data by ID
    - Fetching sensors by location
    - API key authentication
    """
    
    BASE_URL = "https://api.purpleair.com/v1"
    
    def __init__(self, api_key: str):
        """Initialize client.
        
        Args:
            api_key: PurpleAir API key
        """
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "X-API-Key": self.api_key,
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client
    
    async def get_sensor(self, sensor_id: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific sensor.
        
        Args:
            sensor_id: PurpleAir sensor ID
            
        Returns:
            Sensor data dictionary or None
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/sensors/{sensor_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch sensor {sensor_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching sensor {sensor_id}: {e}")
            return None
    
    async def get_sensors_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
    ) -> list[Dict[str, Any]]:
        """Get sensors near a location.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            
        Returns:
            List of sensor data
        """
        try:
            client = await self._get_client()
            
            # Convert km to meters for API
            radius_m = radius_km * 1000
            
            response = await client.get(
                "/sensors",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "radius": radius_m,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.warning(f"Failed to fetch sensors by location: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching sensors by location: {e}")
            return []
    
    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            client = await self._get_client()
            response = await client.get("/metadata")
            return response.status_code in (200, 401, 403)
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
