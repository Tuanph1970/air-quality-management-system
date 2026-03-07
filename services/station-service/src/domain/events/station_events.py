"""Domain events for the station service."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from shared.events.base_event import DomainEvent


@dataclass
class StationCreated(DomainEvent):
    """Event emitted when a new station is created."""
    
    station_id: UUID
    station_code: str
    name: str
    station_type: str
    latitude: float
    longitude: float
    event_type: str = "station.created"


@dataclass
class StationActivated(DomainEvent):
    """Event emitted when a station is activated."""
    
    station_id: UUID
    event_type: str = "station.activated"


@dataclass
class StationDeactivated(DomainEvent):
    """Event emitted when a station is deactivated."""
    
    station_id: UUID
    reason: str = ""
    event_type: str = "station.deactivated"


@dataclass
class StationAPIConfigured(DomainEvent):
    """Event emitted when a station's API is configured."""
    
    station_id: UUID
    endpoint: str
    adapter_type: str
    poll_interval: int
    event_type: str = "station.api.configured"


@dataclass
class StationDataReceived(DomainEvent):
    """Event emitted when data is received from a station.
    
    This event triggers AQI recalculation in the air-quality-service.
    """
    
    station_id: UUID
    timestamp: datetime
    source: str = "STATION_API"  # STATION_API, WEBHOOK, MANUAL
    event_type: str = "station.data.received"


@dataclass
class StationReadingsCreated(DomainEvent):
    """Event emitted when new readings are recorded.
    
    Contains the actual reading values for downstream processing.
    """
    
    station_id: UUID
    readings: Dict[str, float]  # pollutant_name -> value
    timestamp: datetime
    source: str = "STATION_API"
    event_type: str = "station.readings.created"


@dataclass
class StationDataValidationFailed(DomainEvent):
    """Event emitted when station data validation fails."""
    
    station_id: UUID
    reason: str
    invalid_data: Optional[Dict[str, Any]] = None
    event_type: str = "station.data.validation_failed"
