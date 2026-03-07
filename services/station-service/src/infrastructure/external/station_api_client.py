"""Station API client - orchestrates data fetching from station APIs."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .adapters.base_adapter import StationDataResult
from .adapters.factory import AdapterFactory, get_adapter

logger = logging.getLogger(__name__)


class StationAPIClient:
    """Client for fetching data from station APIs.
    
    This client uses the Strategy pattern to support different
    API adapters for various station types.
    
    Example:
        client = StationAPIClient()
        result = await client.fetch_data(station_config)
        if result.success:
            readings = result.readings
    """
    
    def __init__(self, adapter_factory: Optional[AdapterFactory] = None):
        """Initialize station API client.
        
        Args:
            adapter_factory: Optional custom adapter factory
        """
        self.adapter_factory = adapter_factory or AdapterFactory.get_instance()
    
    async def fetch_data(self, config: Dict[str, Any]) -> StationDataResult:
        """Fetch data from a station API.
        
        Args:
            config: Station API configuration including:
                - endpoint: API URL
                - method: HTTP method
                - headers: HTTP headers
                - auth_type: Authentication type
                - auth_credentials: Authentication credentials
                - adapter_type: Adapter type (default: "generic")
                - poll_interval_seconds: Polling interval
                - response_mapping: How to map response to readings
            
        Returns:
            StationDataResult with readings or error
        """
        adapter_type = config.get("adapter_type", "generic")
        
        try:
            adapter = self.adapter_factory.create(adapter_type)
        except ValueError as e:
            logger.error(f"Failed to create adapter: {e}")
            return StationDataResult.error_result(str(e))
        
        # Validate config
        is_valid, error = adapter.validate_config(config)
        if not is_valid:
            return StationDataResult.error_result(f"Invalid config: {error}")
        
        # Fetch data
        logger.info(
            f"Fetching data from station API using {adapter_type} adapter"
        )
        result = await adapter.fetch_data(config)
        
        if result.success:
            logger.info(
                f"Successfully fetched {len(result.readings)} readings"
            )
        else:
            logger.warning(f"Failed to fetch station data: {result.error}")
        
        return result
    
    async def test_connection(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """Test connection to a station API.
        
        Args:
            config: Station API configuration
            
        Returns:
            Tuple of (success, message)
        """
        adapter_type = config.get("adapter_type", "generic")
        
        try:
            adapter = self.adapter_factory.create(adapter_type)
        except ValueError as e:
            return False, f"Invalid adapter type: {e}"
        
        is_valid, error = adapter.validate_config(config)
        if not is_valid:
            return False, f"Invalid config: {error}"
        
        success = await adapter.test_connection(config)
        
        if success:
            return True, f"Connection successful using {adapter_type} adapter"
        else:
            return False, "Connection failed"
    
    def should_poll(self, config: Dict[str, Any], last_fetch: Optional[datetime]) -> bool:
        """Check if it's time to poll the API.
        
        Args:
            config: Station API configuration
            last_fetch: When data was last fetched
            
        Returns:
            True if should poll now
        """
        poll_interval = config.get("poll_interval_seconds", 300)
        
        if last_fetch is None:
            return True
        
        next_poll = last_fetch + timedelta(seconds=poll_interval)
        return datetime.utcnow() >= next_poll
