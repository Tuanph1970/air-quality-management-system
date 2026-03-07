"""Station entity - the core aggregate root of the station bounded context.

Encapsulates identity, configuration, geographic location, and lifecycle state
for air quality monitoring stations. All state mutations go through explicit
methods that enforce invariants and record events for downstream consumers.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..events.station_events import (
    StationCreated,
    StationActivated,
    StationDeactivated,
    StationAPIConfigured,
    StationDataReceived,
)
from ..exceptions.station_exceptions import (
    StationAlreadyActiveError,
    StationOfflineError,
    InvalidStationConfigurationError,
)
from ..value_objects.station_type import StationType
from ..value_objects.geographic_coordinate import GeographicCoordinate


@dataclass
class Station:
    """Aggregate root representing an air quality monitoring station.
    
    Identity is defined by ``id`` (UUID). ``station_code`` is a natural key
    that must be unique across the system (e.g., government station ID).
    
    Attributes:
        id: Unique identifier (UUID)
        station_code: External/natural identifier (e.g., EPA station ID)
        name: Human-readable station name
        station_type: Classification of station
        location: Geographic coordinates
        api_config: API configuration for data fetching
        is_active: Whether station is actively reporting data
        data_retention_days: How long to retain readings (default: 1 day)
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        last_data_received: Timestamp of last data reception
    """
    
    id: UUID = field(default_factory=uuid4)
    station_code: str = ""
    name: str = ""
    station_type: StationType = StationType.URBAN
    location: GeographicCoordinate = field(default_factory=lambda: GeographicCoordinate(0.0, 0.0))
    api_config: Optional[Dict[str, Any]] = None
    is_active: bool = False
    data_retention_days: int = 1  # Default: 1 day as per requirements
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_data_received: Optional[datetime] = None
    
    _events: List = field(default_factory=list, repr=False)
    
    # ------------------------------------------------------------------
    # Factory method (named-constructor pattern)
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        name: str,
        station_code: str,
        station_type: str | StationType,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
        data_retention_days: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Station":
        """Create a new air quality monitoring station.
        
        Args:
            name: Human-readable station name
            station_code: Unique external identifier (e.g., EPA station ID)
            station_type: Station classification
            latitude: GPS latitude (-90 to 90)
            longitude: GPS longitude (-180 to 180)
            altitude: Optional altitude in meters
            data_retention_days: Days to retain data (default: 1)
            metadata: Optional additional metadata
            
        Returns:
            New Station instance
            
        Raises:
            InvalidStationConfigurationError: If configuration is invalid
        """
        if not name or not name.strip():
            raise InvalidStationConfigurationError("Station name cannot be empty")
        if not station_code or not station_code.strip():
            raise InvalidStationConfigurationError("Station code cannot be empty")
        if not -90.0 <= latitude <= 90.0:
            raise InvalidStationConfigurationError(f"Invalid latitude: {latitude}")
        if not -180.0 <= longitude <= 180.0:
            raise InvalidStationConfigurationError(f"Invalid longitude: {longitude}")
        if data_retention_days < 1:
            raise InvalidStationConfigurationError("Data retention days must be at least 1")
        
        # Coerce string to enum
        if isinstance(station_type, str):
            station_type = StationType.from_string(station_type)
        
        now = datetime.now(timezone.utc)
        station = cls(
            id=uuid4(),
            station_code=station_code.strip(),
            name=name.strip(),
            station_type=station_type,
            location=GeographicCoordinate.create(latitude, longitude, altitude),
            api_config=None,
            is_active=False,
            data_retention_days=data_retention_days,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            last_data_received=None,
        )
        
        station._events.append(
            StationCreated(
                station_id=station.id,
                station_code=station.station_code,
                name=station.name,
                station_type=station.station_type.value,
                latitude=latitude,
                longitude=longitude,
            )
        )
        
        return station
    
    # ------------------------------------------------------------------
    # Command methods (state mutations)
    # ------------------------------------------------------------------
    def configure_api(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        auth_type: str = "none",
        auth_credentials: Optional[Dict[str, str]] = None,
        poll_interval_seconds: int = 300,
        adapter_type: str = "generic",
        request_template: Optional[Dict[str, Any]] = None,
        response_mapping: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Configure API endpoint for automatic data collection.
        
        Args:
            endpoint: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            headers: Optional HTTP headers
            auth_type: Authentication type (none, basic, bearer, api_key)
            auth_credentials: Authentication credentials
            poll_interval_seconds: How often to poll the API
            adapter_type: API adapter type (generic, epa, etc.)
            request_template: Optional request body template
            response_mapping: Mapping from API response to internal format
            
        Raises:
            InvalidStationConfigurationError: If API config is invalid
        """
        if not endpoint or not endpoint.strip():
            raise InvalidStationConfigurationError("API endpoint cannot be empty")
        if not endpoint.startswith(("http://", "https://")):
            raise InvalidStationConfigurationError(
                "API endpoint must start with http:// or https://"
            )
        if method.upper() not in ("GET", "POST", "PUT", "PATCH"):
            raise InvalidStationConfigurationError(f"Invalid HTTP method: {method}")
        if poll_interval_seconds < 10:
            raise InvalidStationConfigurationError(
                "Poll interval must be at least 10 seconds"
            )
        
        self.api_config = {
            "endpoint": endpoint.strip(),
            "method": method.upper(),
            "headers": headers or {},
            "auth_type": auth_type.lower(),
            "auth_credentials": auth_credentials or {},
            "poll_interval_seconds": poll_interval_seconds,
            "adapter_type": adapter_type.lower(),
            "request_template": request_template,
            "response_mapping": response_mapping,
        }
        self.updated_at = datetime.now(timezone.utc)
        
        self._events.append(
            StationAPIConfigured(
                station_id=self.id,
                endpoint=endpoint,
                adapter_type=adapter_type,
                poll_interval=poll_interval_seconds,
            )
        )
    
    def activate(self) -> None:
        """Activate the station for data collection.
        
        Raises:
            StationAlreadyActiveError: If station is already active
            InvalidStationConfigurationError: If station is not properly configured
        """
        if self.is_active:
            raise StationAlreadyActiveError(str(self.id))
        
        if not self.api_config:
            raise InvalidStationConfigurationError(
                "Cannot activate station without API configuration"
            )
        
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
        
        self._events.append(
            StationActivated(station_id=self.id)
        )
    
    def deactivate(self, reason: str = "") -> None:
        """Deactivate the station.
        
        Args:
            reason: Optional reason for deactivation
        """
        if not self.is_active:
            return  # Already inactive
        
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
        
        self._events.append(
            StationDeactivated(
                station_id=self.id,
                reason=reason,
            )
        )
    
    def record_data_received(self) -> None:
        """Record that data was successfully received from the station."""
        self.last_data_received = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        self._events.append(
            StationDataReceived(
                station_id=self.id,
                timestamp=self.last_data_received,
            )
        )
    
    def update(
        self,
        name: Optional[str] = None,
        station_type: Optional[str | StationType] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        altitude: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        data_retention_days: Optional[int] = None,
    ) -> None:
        """Update station properties.
        
        Only non-None arguments are applied.
        
        Args:
            name: New station name
            station_type: New station type
            latitude: New latitude
            longitude: New longitude
            altitude: New altitude
            metadata: Additional metadata to merge
            data_retention_days: New retention period
        """
        if name is not None:
            if not name.strip():
                raise InvalidStationConfigurationError("Station name cannot be empty")
            self.name = name.strip()
        
        if station_type is not None:
            if isinstance(station_type, str):
                station_type = StationType.from_string(station_type)
            self.station_type = station_type
        
        if latitude is not None or longitude is not None:
            lat = latitude if latitude is not None else self.location.latitude
            lng = longitude if longitude is not None else self.location.longitude
            alt = altitude if altitude is not None else self.location.altitude
            self.location = GeographicCoordinate.create(lat, lng, alt)
        
        if metadata is not None:
            self.metadata.update(metadata)
        
        if data_retention_days is not None:
            if data_retention_days < 1:
                raise InvalidStationConfigurationError(
                    "Data retention days must be at least 1"
                )
            self.data_retention_days = data_retention_days
        
        self.updated_at = datetime.now(timezone.utc)
    
    def update_api_config(self, config: Dict[str, Any]) -> None:
        """Update API configuration partially.
        
        Args:
            config: Dictionary of config fields to update
        """
        if self.api_config is None:
            self.api_config = {}
        
        allowed_fields = {
            "endpoint", "method", "headers", "auth_type",
            "auth_credentials", "poll_interval_seconds",
            "adapter_type", "request_template", "response_mapping",
        }
        
        for key, value in config.items():
            if key in allowed_fields:
                self.api_config[key] = value
        
        self.updated_at = datetime.now(timezone.utc)
    
    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    @property
    def is_configured(self) -> bool:
        """Return True if station has API configuration."""
        return self.api_config is not None
    
    @property
    def can_collect_data(self) -> bool:
        """Return True if station can collect data."""
        return self.is_active and self.is_configured
    
    @property
    def poll_interval(self) -> int:
        """Get polling interval in seconds."""
        if self.api_config:
            return self.api_config.get("poll_interval_seconds", 300)
        return 300  # Default 5 minutes
    
    @property
    def adapter_type(self) -> str:
        """Get API adapter type."""
        if self.api_config:
            return self.api_config.get("adapter_type", "generic")
        return "generic"
    
    # ------------------------------------------------------------------
    # Event collection
    # ------------------------------------------------------------------
    def collect_events(self) -> List:
        """Return and clear accumulated domain events."""
        events = self._events.copy()
        self._events.clear()
        return events
