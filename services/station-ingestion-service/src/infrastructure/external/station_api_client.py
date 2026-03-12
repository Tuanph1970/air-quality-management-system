"""Client for external station API (admin-qttd.tedp.vn)."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.core.config import config

logger = logging.getLogger(__name__)


class StationAPIClient:
    """Client for the external environmental monitoring station API.

    API Documentation: https://admin-qttd.tedp.vn/api/partner/v1

    Endpoints:
    - GET /get-automation-stations: List all automation stations
    - GET /aqi_hours: Get hourly AQI data by station codes
    """

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
    ):
        """Initialize the API client.

        Args:
            base_url: Base URL of the station API
            api_key: API key for authentication
        """
        self.base_url = (base_url or config.STATION_API_BASE_URL).rstrip("/")
        self.api_key = api_key or config.STATION_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication headers."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-API-KEY": self.api_key,
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_automation_stations(
        self,
        page: int = 0,
        size: int = 100,
        api_type: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """Get list of automation stations.

        Args:
            page: Page number (0-indexed)
            size: Number of records per page
            api_type: API type (usually 1)

        Returns:
            Response data with station list or None if failed

        API Response structure:
        {
            "content": [
                {
                    "stationCode": "LSOS_KHIKHO",
                    "stationName": "Khanh Hoa: Vinh Hoa Ward - Nha Trang (KK)",
                    "address": "SOS Children's Village Nha Trang Campus...",
                    "latitude": 12.284358,
                    "longitude": 109.192524,
                    "stationType": 4,
                    "provinceId": "2844..."
                }
            ],
            "pageable": {...},
            "totalElements": 26,
            "totalPages": 1
        }
        """
        try:
            client = await self._get_client()
            response = await client.get(
                "/get-automation-stations",
                params={
                    "page": page,
                    "size": size,
                    "apiType": api_type,
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch stations: {response.status_code} - {response.text[:200]}"
                )
                return None

        except httpx.TimeoutException:
            logger.error("Timeout fetching stations")
            return None
        except Exception as e:
            logger.error(f"Error fetching stations: {e}", exc_info=True)
            return None

    async def get_aqi_hours(
        self,
        from_time: datetime,
        to_time: datetime,
        page: int = 0,
        size: int = 100,
        api_type: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """Get hourly AQI data for stations.

        Args:
            from_time: Start time for data retrieval
            to_time: End time for data retrieval
            page: Page number (0-indexed)
            size: Number of records per page
            api_type: API type (usually 1)

        Returns:
            Response data with AQI readings by station code or None if failed

        API Response structure:
        {
            "content": [
                {
                    "HCM_THDI_KHIKXQ": [
                        {
                            "id": "6931318bb93db...",
                            "getTime": "2025-12-04T00:00:00",
                            "stationId": "324818...",
                            "data": {
                                "aqi": 50.5,
                                "PM2.5": 50.5,
                                "PM10": 45.08,
                                "CO": 16.22,
                                "SO2": 0.68,
                                "NO2": 5.63,
                                "O3": 12.24,
                                "Temp": null,
                                "RH": null
                            }
                        }
                    ],
                    "LSOS_KHIKHO": [...]
                }
            ],
            "pageable": {...}
        }
        """
        try:
            client = await self._get_client()

            # Format datetime as ISO string
            from_str = from_time.strftime("%Y-%m-%dT%H:%M:%S")
            to_str = to_time.strftime("%Y-%m-%dT%H:%M:%S")

            response = await client.get(
                "/aqi_hours",
                params={
                    "page": page,
                    "size": size,
                    "apiType": api_type,
                    "from": from_str,
                    "to": to_str,
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to fetch AQI hours: {response.status_code} - {response.text[:200]}"
                )
                return None

        except httpx.TimeoutException:
            logger.error("Timeout fetching AQI hours data")
            return None
        except Exception as e:
            logger.error(f"Error fetching AQI hours data: {e}", exc_info=True)
            return None

    async def test_connection(self) -> bool:
        """Test API connection by fetching stations."""
        try:
            result = await self.get_automation_stations(page=0, size=1)
            return result is not None
        except Exception:
            return False
