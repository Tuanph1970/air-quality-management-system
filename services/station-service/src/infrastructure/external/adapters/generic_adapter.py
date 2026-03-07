"""Generic station adapter - works with most REST APIs."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from .base_adapter import BaseStationAdapter, StationDataResult

logger = logging.getLogger(__name__)


class GenericStationAdapter(BaseStationAdapter):
    """Generic HTTP adapter for station APIs.
    
    This adapter works with most RESTful station APIs that return
    JSON data. It supports various authentication methods and
    configurable response mapping.
    
    Example config:
        {
            "endpoint": "https://api.example.com/stations/123/readings",
            "method": "GET",
            "headers": {"Accept": "application/json"},
            "auth_type": "bearer",
            "auth_credentials": {"token": "your-token"},
            "response_mapping": {
                "PM25": "data.pm25",
                "PM10": "data.pm10",
                "SO2": {"path": "pollutants.so2.value"},
            }
        }
    """
    
    adapter_type: str = "generic"
    adapter_name: str = "Generic HTTP Station Adapter"
    
    async def fetch_data(self, config: Dict[str, Any]) -> StationDataResult:
        """Fetch data from a generic REST API.
        
        Args:
            config: API configuration
            
        Returns:
            StationDataResult with readings or error
        """
        endpoint = config.get("endpoint", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        auth_type = config.get("auth_type", "none")
        auth_credentials = config.get("auth_credentials", {})
        request_template = config.get("request_template")
        response_mapping = config.get("response_mapping", {})
        
        # Prepare headers
        headers = dict(headers)  # Copy to avoid mutation
        headers.setdefault("Accept", "application/json")
        headers.setdefault("User-Agent", "AQMS-Station-Service/1.0")
        
        # Apply authentication
        if auth_type == "bearer":
            token = auth_credentials.get("token", "")
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            username = auth_credentials.get("username", "")
            password = auth_credentials.get("password", "")
            import base64
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif auth_type == "api_key":
            key_name = auth_credentials.get("key_name", "X-API-Key")
            api_key = auth_credentials.get("api_key", "")
            headers[key_name] = api_key
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Prepare request
                if method == "GET":
                    response = await client.get(endpoint, headers=headers)
                elif method == "POST":
                    body = request_template or {}
                    response = await client.post(endpoint, headers=headers, json=body)
                elif method == "PUT":
                    body = request_template or {}
                    response = await client.put(endpoint, headers=headers, json=body)
                elif method == "PATCH":
                    body = request_template or {}
                    response = await client.patch(endpoint, headers=headers, json=body)
                else:
                    return StationDataResult.error_result(f"Unsupported HTTP method: {method}")
                
                # Handle response
                if response.status_code not in (200, 201):
                    logger.warning(
                        f"API request failed: {response.status_code} - {response.text[:200]}"
                    )
                    return StationDataResult.error_result(
                        f"HTTP {response.status_code}: {response.reason_phrase}",
                        raw_response=response.text,
                    )
                
                # Parse response
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return StationDataResult.error_result(
                        "Invalid JSON response from API",
                        raw_response=response.text,
                    )
                
                # Map response to readings
                readings = self.map_response(data, response_mapping)
                
                if not readings:
                    logger.warning(f"No readings extracted from response: {data}")
                    return StationDataResult.error_result(
                        "No pollutant readings found in response",
                        raw_response=data,
                    )
                
                # Extract timestamp if available
                timestamp = self._extract_timestamp(data, response_mapping)
                
                logger.info(
                    f"Fetched {len(readings)} readings from {endpoint}: {readings}"
                )
                
                return StationDataResult.success_result(
                    readings=readings,
                    timestamp=timestamp,
                    raw_response=data,
                )
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching data from {endpoint}")
            return StationDataResult.error_result("Request timeout")
        except httpx.ConnectError as e:
            logger.error(f"Connection error to {endpoint}: {e}")
            return StationDataResult.error_result(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching data: {e}", exc_info=True)
            return StationDataResult.error_result(f"Unexpected error: {str(e)}")
    
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test API connection with a simple GET request.
        
        Args:
            config: API configuration
            
        Returns:
            True if connection successful
        """
        endpoint = config.get("endpoint", "")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(endpoint)
                return response.status_code in (200, 201, 401, 403)
                # 401/403 means server is reachable, just need auth
        except Exception:
            return False
    
    def _extract_timestamp(
        self,
        data: Dict[str, Any],
        response_mapping: Dict[str, Any],
    ) -> Optional[datetime]:
        """Extract timestamp from response.
        
        Args:
            data: Response data
            response_mapping: Mapping configuration
            
        Returns:
            Extracted timestamp or None
        """
        # Check for timestamp in mapping
        if isinstance(response_mapping, dict):
            ts_mapping = response_mapping.get("_timestamp")
            if ts_mapping:
                value = self._extract_value(data, {"path": ts_mapping})
                if value:
                    try:
                        # Try to parse as ISO format or Unix timestamp
                        if isinstance(value, (int, float)):
                            return datetime.fromtimestamp(value)
                        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                    except Exception:
                        pass
        
        # Try common timestamp keys
        for key in ["timestamp", "datetime", "time", "date", "measured_at", "created_at"]:
            if key in data:
                try:
                    value = data[key]
                    if isinstance(value, (int, float)):
                        return datetime.fromtimestamp(value)
                    return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                except Exception:
                    continue
        
        return None
