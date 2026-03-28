"""EnviSoft adapter - fetches raw 5-minute interval data from EnviSoft API.

This adapter handles the specific API endpoint for minute-level data from EnviSoft.
It supports pagination to capture all records within a date range.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from .base_adapter import BaseStationAdapter, StationDataResult

logger = logging.getLogger(__name__)


class EnviSoftAdapter(BaseStationAdapter):
    """Adapter for EnviSoft API to fetch raw 5-minute interval station data.

    This adapter specifically targets the data-average-by-time endpoint which
    returns minute-level pollutant and environmental data.

    Expected API response structure:
    {
        "_embedded": {
            "dataAverageByTimeList": [
                {
                    "getTime": "2026-03-01T00:05:00Z",
                    "no": 10.5,
                    "o3": 25.3,
                    "co": 0.5,
                    "no2": 15.2,
                    "nox": 25.7,
                    "so2": 5.1,
                    "pm10": 45.0,
                    "pm25": 25.0,
                    "temperature": 28.5,
                    "humidity": 65.0,
                    "pressure": 1013.25,
                    "windspeed": 2.5,
                    "winddirection": 180.0,
                    ...
                },
                ...
            ]
        },
        "page": {
            "size": 500,
            "totalElements": 10000,
            "totalPages": 20,
            "number": 0
        }
    }

    Example config:
        {
            "endpoint": "https://admin-qttd.tedp.vn/api/eos/data-average-by-time",
            "station_id": "32481806727101955692134278002",
            "from_date": "2026-03-01",
            "to_date": "2026-03-02",
            "time_type": "5 phút",  # 5 minutes
            "headers": {...},
            "auth_type": "cookie",
            "auth_credentials": {
                "cookies": {"JSESSIONID": "..."}
            }
        }
    """

    adapter_type: str = "envisoft"
    adapter_name: str = "EnviSoft 5-Minute Data Adapter"

    def __init__(self):
        """Initialize EnviSoft adapter."""
        self.client: Optional[httpx.AsyncClient] = None

    async def fetch_data(self, config: Dict[str, Any]) -> StationDataResult:
        """Fetch raw 5-minute data from EnviSoft API.

        Args:
            config: API configuration including:
                - endpoint: Base API URL
                - station_id: EnviSoft station ID
                - from_date: Start date (YYYY-MM-DD)
                - to_date: End date (YYYY-MM-DD)
                - time_type: Time interval type (default: "5 phút")
                - headers: HTTP headers
                - auth_type: Authentication type
                - auth_credentials: Auth credentials including cookies

        Returns:
            StationDataResult with raw data records or error
        """
        endpoint = config.get("endpoint", "")
        station_id = config.get("station_id", "")
        from_date = config.get("from_date", "")
        to_date = config.get("to_date", "")
        time_type = config.get("time_type", "5 phút")

        if not endpoint or not station_id:
            return StationDataResult.error_result(
                "EnviSoft endpoint and station_id are required"
            )

        all_records: List[Dict[str, Any]] = []
        page = 0
        page_size = 500
        max_pages = 1000  # Safety limit

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                while page < max_pages:
                    # Build API URL with pagination
                    params = self._build_params(
                        station_id=station_id,
                        from_date=from_date,
                        to_date=to_date,
                        time_type=time_type,
                        page=page,
                        size=page_size,
                    )

                    headers = self._build_headers(config)
                    auth_headers = await self._build_auth_headers(config)

                    full_headers = {**headers, **auth_headers}

                    logger.info(
                        f"Fetching EnviSoft data: page={page}, station={station_id[:20]}..."
                    )

                    response = await client.get(endpoint, params=params, headers=full_headers)

                    if response.status_code == 401:
                        return StationDataResult.error_result(
                            "Authentication failed - please login to EnviSoft",
                            raw_response=response.text,
                        )
                    elif response.status_code != 200:
                        return StationDataResult.error_result(
                            f"HTTP {response.status_code}: {response.reason_phrase}",
                            raw_response=response.text[:500],
                        )

                    # Parse response
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        return StationDataResult.error_result(
                            "Invalid JSON response from EnviSoft API",
                            raw_response=response.text[:500],
                        )

                    # Extract records from embedded list
                    records = self._extract_records(data)
                    if not records:
                        logger.info(f"No more records at page {page}")
                        break

                    all_records.extend(records)
                    logger.info(f"  Page {page}: {len(records)} records (total: {len(all_records)})")

                    # Check pagination info
                    pagination = data.get("page", {})
                    total_pages = pagination.get("totalPages", 1)
                    current_page = pagination.get("number", page)

                    if current_page >= total_pages - 1:
                        logger.info(f"Reached last page (page {current_page} of {total_pages - 1})")
                        break

                    page += 1

                if not all_records:
                    return StationDataResult.error_result(
                        "No data returned from EnviSoft API",
                    )

                logger.info(f"Successfully fetched {len(all_records)} total records")

                # Extract timestamp from first record (for compatibility)
                timestamp = None
                if all_records:
                    ts_str = all_records[0].get("getTime") or all_records[0].get("time")
                    if ts_str:
                        try:
                            timestamp = datetime.fromisoformat(
                                ts_str.replace("Z", "+00:00")
                            )
                        except ValueError:
                            pass

                return StationDataResult.success_result(
                    readings={},  # No single readings dict for raw data
                    timestamp=timestamp,
                    raw_response=all_records,
                    metadata={
                        "total_records": len(all_records),
                        "station_id": station_id,
                        "from_date": from_date,
                        "to_date": to_date,
                        "pages_fetched": page + 1,
                    },
                )

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching from EnviSoft: {endpoint}")
            return StationDataResult.error_result("Request timeout from EnviSoft API")
        except httpx.ConnectError as e:
            logger.error(f"Connection error to EnviSoft: {e}")
            return StationDataResult.error_result(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching EnviSoft data: {e}", exc_info=True)
            return StationDataResult.error_result(f"Unexpected error: {str(e)}")

    def _build_params(
        self,
        station_id: str,
        from_date: str,
        to_date: str,
        time_type: str,
        page: int,
        size: int,
    ) -> Dict[str, Any]:
        """Build API request parameters.

        Args:
            station_id: EnviSoft station ID
            from_date: Start date
            to_date: End date
            time_type: Time interval type
            page: Page number (0-indexed)
            size: Page size

        Returns:
            Dictionary of query parameters
        """
        return {
            "stationId": station_id,
            "fromDate": from_date,
            "toDate": to_date,
            "timeType": time_type,
            "page": page,
            "size": size,
        }

    def _build_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers.

        Args:
            config: API configuration

        Returns:
            Dictionary of HTTP headers
        """
        headers = dict(config.get("headers", {}))
        headers.setdefault("Accept", "application/json")
        headers.setdefault("User-Agent", "AQMS-Station-Service/1.0")
        return headers

    async def _build_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Build authentication headers.

        Args:
            config: API configuration including auth_credentials

        Returns:
            Dictionary of authentication headers
        """
        auth_type = config.get("auth_type", "none")
        auth_credentials = config.get("auth_credentials", {})

        if auth_type == "cookie":
            cookies = auth_credentials.get("cookies", {})
            # For cookie auth, we return empty dict as cookies are handled separately
            return {}
        elif auth_type == "bearer":
            token = auth_credentials.get("token", "")
            return {"Authorization": f"Bearer {token}"}
        elif auth_type == "basic":
            username = auth_credentials.get("username", "")
            password = auth_credentials.get("password", "")
            import base64
            credentials = base64.b64encode(
                f"{username}:{password}".encode()
            ).decode()
            return {"Authorization": f"Basic {credentials}"}
        elif auth_type == "api_key":
            key_name = auth_credentials.get("key_name", "X-API-Key")
            api_key = auth_credentials.get("api_key", "")
            return {key_name: api_key}

        return {}

    def _extract_records(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract data records from API response.

        Args:
            data: API response JSON

        Returns:
            List of data records
        """
        # Handle HAL-style _embedded response
        embedded = data.get("_embedded", {})
        if isinstance(embedded, dict):
            records = embedded.get("dataAverageByTimeList", [])
            if isinstance(records, list):
                return records

        # Handle direct array response
        if isinstance(data, list):
            return data

        return []

    def map_response(
        self,
        response: Any,
        response_mapping: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Map EnviSoft response to pollutant readings.

        Note: For raw data, this returns an empty dict since we store
        the complete raw response. Use _extract_records() instead.
        """
        return {}

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test connection to EnviSoft API.

        Args:
            config: API configuration

        Returns:
            True if connection successful
        """
        endpoint = config.get("endpoint", "")

        if not endpoint:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try a simple request
                params = {
                    "page": 0,
                    "size": 1,
                }
                response = await client.get(endpoint, params=params)
                # Accept various status codes as "reachable"
                return response.status_code in (200, 401, 403)
        except Exception:
            return False

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate EnviSoft API configuration.

        Args:
            config: API configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not config.get("endpoint"):
            return False, "EnviSoft API endpoint is required"

        if not config.get("station_id"):
            return False, "EnviSoft station_id is required"

        endpoint = config["endpoint"]
        if not endpoint.startswith(("http://", "https://")):
            return False, "Endpoint must start with http:// or https://"

        return True, None
