"""Base adapter - Strategy pattern for station API adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class StationDataResult:
    """Result from fetching station data.
    
    Attributes:
        success: Whether the fetch was successful
        readings: Dictionary of pollutant_name -> value
        timestamp: When the data was measured
        raw_response: Original API response for debugging
        error: Error message if failed
        metadata: Additional metadata from the API
    """
    
    success: bool
    readings: Dict[str, float] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    raw_response: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success_result(
        cls,
        readings: Dict[str, float],
        timestamp: Optional[datetime] = None,
        raw_response: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "StationDataResult":
        """Create a successful result."""
        return cls(
            success=True,
            readings=readings,
            timestamp=timestamp or datetime.utcnow(),
            raw_response=raw_response,
            metadata=metadata or {},
        )
    
    @classmethod
    def error_result(
        cls,
        error: str,
        raw_response: Any = None,
    ) -> "StationDataResult":
        """Create an error result."""
        return cls(
            success=False,
            error=error,
            raw_response=raw_response,
        )


class BaseStationAdapter(ABC):
    """Abstract base class for station API adapters (Strategy pattern).
    
    This defines the interface that all station API adapters must implement.
    Different stations/APIs can have their own adapter implementation.
    
    Example:
        class EPAAdapter(BaseStationAdapter):
            async def fetch_data(self, config):
                # Implement EPA API specific logic
                pass
    """
    
    adapter_type: str = "base"
    adapter_name: str = "Base Station Adapter"
    
    @abstractmethod
    async def fetch_data(self, config: Dict[str, Any]) -> StationDataResult:
        """Fetch data from a station API.
        
        Args:
            config: API configuration including:
                - endpoint: API URL
                - method: HTTP method
                - headers: HTTP headers
                - auth_type: Authentication type
                - auth_credentials: Authentication credentials
                - request_template: Optional request body template
                - response_mapping: How to map response to readings
            
        Returns:
            StationDataResult with readings or error
        """
        pass
    
    @abstractmethod
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test if the API connection works.
        
        Args:
            config: API configuration
            
        Returns:
            True if connection successful
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate API configuration.
        
        Args:
            config: API configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not config.get("endpoint"):
            return False, "API endpoint is required"
        
        endpoint = config["endpoint"]
        if not endpoint.startswith(("http://", "https://")):
            return False, "Endpoint must start with http:// or https://"
        
        return True, None
    
    def map_response(
        self,
        response: Any,
        response_mapping: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Map API response to pollutant readings.
        
        Args:
            response: Raw API response
            response_mapping: Mapping configuration
            
        Returns:
            Dictionary of pollutant_name -> value
        """
        if not response_mapping:
            # Default: try to extract common pollutant keys
            return self._extract_default_readings(response)
        
        readings = {}
        
        for pollutant, mapping in response_mapping.items():
            value = self._extract_value(response, mapping)
            if value is not None:
                readings[pollutant] = value
        
        return readings
    
    def _extract_default_readings(self, response: Any) -> Dict[str, float]:
        """Extract readings using common key names."""
        readings = {}
        
        if isinstance(response, dict):
            # Common pollutant key patterns
            pollutant_keys = {
                "pm25": ["pm25", "PM25", "pm2_5", "PM2.5"],
                "pm10": ["pm10", "PM10"],
                "so2": ["so2", "SO2"],
                "nox": ["nox", "NOX"],
                "no2": ["no2", "NO2"],
                "co": ["co", "CO"],
                "co2": ["co2", "CO2"],
                "o3": ["o3", "O3"],
            }
            
            for pollutant, keys in pollutant_keys.items():
                for key in keys:
                    if key in response:
                        try:
                            readings[pollutant.upper()] = float(response[key])
                            break
                        except (ValueError, TypeError):
                            continue
        
        return readings
    
    def _extract_value(
        self,
        data: Any,
        mapping: Dict[str, Any],
    ) -> Optional[float]:
        """Extract a value from response using mapping.
        
        Args:
            data: Response data
            mapping: Mapping config with 'path' or 'key'
            
        Returns:
            Extracted value or None
        """
        if isinstance(mapping, str):
            # Simple key mapping
            if isinstance(data, dict) and mapping in data:
                try:
                    return float(data[mapping])
                except (ValueError, TypeError):
                    return None
        
        elif isinstance(mapping, dict):
            path = mapping.get("path", mapping.get("key"))
            if path and isinstance(data, dict):
                # Support nested paths like "data.readings.pm25"
                value = data
                for key in path.split("."):
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return None
                
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
        
        return None
