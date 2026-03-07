"""Application commands - Write operations (CQRS)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class CreateStationCommand:
    """Command to create a new air quality station."""
    
    name: str
    station_code: str
    station_type: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    data_retention_days: int = 1
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateStationCommand:
    """Command to update station properties."""
    
    station_id: UUID
    name: Optional[str] = None
    station_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    data_retention_days: Optional[int] = None


@dataclass
class ConfigureStationAPICommand:
    """Command to configure station API endpoint."""
    
    station_id: UUID
    endpoint: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    auth_type: str = "none"
    auth_credentials: Optional[Dict[str, str]] = None
    poll_interval_seconds: int = 300
    adapter_type: str = "generic"
    request_template: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, Any]] = None


@dataclass
class ActivateStationCommand:
    """Command to activate a station."""
    
    station_id: UUID


@dataclass
class DeactivateStationCommand:
    """Command to deactivate a station."""
    
    station_id: UUID
    reason: str = ""


@dataclass
class IngestStationDataCommand:
    """Command to ingest data from a station API."""
    
    station_id: UUID
    force: bool = False  # Force ingestion even if not due


@dataclass
class RecordStationReadingsCommand:
    """Command to record readings from a station (webhook/manual)."""
    
    station_id: UUID
    readings: Dict[str, float]
    timestamp: Optional[str] = None
    source: str = "API"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeleteStationCommand:
    """Command to delete a station."""
    
    station_id: UUID
