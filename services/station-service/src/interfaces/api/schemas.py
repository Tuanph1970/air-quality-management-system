"""Pydantic schemas for station API request/response."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Request schemas
# =============================================================================

class StationCreateRequest(BaseModel):
    """Payload for creating a new station."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Downtown Monitoring Station",
                "station_code": "EPA-001",
                "station_type": "URBAN",
                "latitude": 21.0285,
                "longitude": 105.8542,
                "altitude": 15.0,
                "data_retention_days": 1,
                "metadata": {"agency": "EPA", "region": "North"},
            }
        }
    )
    
    name: str = Field(..., min_length=1, max_length=255, description="Station name")
    station_code: str = Field(..., min_length=1, max_length=100, description="Unique external station code")
    station_type: str = Field(
        ..., min_length=1, max_length=50,
        description="Station type (GOVERNMENT, INDUSTRIAL, URBAN, RURAL, TRAFFIC, BACKGROUND)",
    )
    latitude: float = Field(..., ge=-90, le=90, description="GPS latitude")
    longitude: float = Field(..., ge=-180, le=180, description="GPS longitude")
    altitude: Optional[float] = Field(None, ge=-500, description="Optional altitude in meters")
    data_retention_days: int = Field(1, ge=1, description="Days to retain data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class StationUpdateRequest(BaseModel):
    """Payload for updating a station."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Station Name",
                "station_type": "GOVERNMENT",
                "latitude": 21.0300,
                "longitude": 105.8600,
            }
        }
    )
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    station_type: Optional[str] = Field(None, min_length=1, max_length=50)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = Field(None, ge=-500)
    metadata: Optional[Dict[str, Any]] = None
    data_retention_days: Optional[int] = Field(None, ge=1)


class StationAPIConfigureRequest(BaseModel):
    """Payload for configuring station API endpoint."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "https://api.example.com/stations/123/readings",
                "method": "GET",
                "headers": {"Accept": "application/json"},
                "auth_type": "bearer",
                "auth_credentials": {"token": "your-api-token"},
                "poll_interval_seconds": 300,
                "adapter_type": "generic",
                "response_mapping": {
                    "PM25": "data.pm25",
                    "PM10": "data.pm10",
                    "SO2": {"path": "pollutants.so2.value"},
                },
            }
        }
    )
    
    endpoint: str = Field(..., min_length=1, description="API endpoint URL")
    method: str = Field("GET", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    auth_type: str = Field("none", description="Authentication type (none, basic, bearer, api_key)")
    auth_credentials: Optional[Dict[str, str]] = Field(None, description="Authentication credentials")
    poll_interval_seconds: int = Field(300, ge=10, description="Polling interval in seconds")
    adapter_type: str = Field("generic", description="Adapter type")
    request_template: Optional[Dict[str, Any]] = Field(None, description="Request body template")
    response_mapping: Optional[Dict[str, Any]] = Field(None, description="Response mapping")


class StationRecordReadingsRequest(BaseModel):
    """Payload for recording station readings (webhook/manual)."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "readings": {
                    "PM25": 35.5,
                    "PM10": 50.0,
                    "SO2": 10.0,
                    "NOX": 40.0,
                    "CO": 5.2,
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "source": "WEBHOOK",
            }
        }
    )
    
    readings: Dict[str, float] = Field(..., description="Pollutant readings")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp")
    source: str = Field("API", description="Data source (API, WEBHOOK, MANUAL)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# =============================================================================
# Response schemas
# =============================================================================

class StationResponse(BaseModel):
    """Single station resource."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    station_code: str
    name: str
    station_type: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    is_active: bool
    is_configured: bool
    api_endpoint: Optional[str] = None
    poll_interval_seconds: Optional[int] = None
    data_retention_days: int
    last_data_received: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dto(cls, dto) -> "StationResponse":
        """Create from DTO."""
        return cls(
            id=dto.id,
            station_code=dto.station_code,
            name=dto.name,
            station_type=dto.station_type,
            latitude=dto.latitude,
            longitude=dto.longitude,
            altitude=dto.altitude,
            is_active=dto.is_active,
            is_configured=dto.is_configured,
            api_endpoint=dto.api_endpoint,
            poll_interval_seconds=dto.poll_interval_seconds,
            data_retention_days=dto.data_retention_days,
            last_data_received=dto.last_data_received,
            metadata=dto.metadata,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class StationListResponse(BaseModel):
    """Paginated list of stations."""
    
    items: List[StationResponse]
    total: int
    skip: int
    limit: int
    
    @classmethod
    def from_dto(cls, dto) -> "StationListResponse":
        """Create from DTO."""
        return cls(
            items=[StationResponse.from_dto(s) for s in dto.items],
            total=dto.total,
            skip=dto.skip,
            limit=dto.limit,
        )


class PollutantReadingResponse(BaseModel):
    """Single pollutant reading."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    station_id: UUID
    pollutant_type: str
    value: float
    unit: str
    quality_flag: Optional[str] = None
    timestamp: datetime
    created_at: datetime
    
    @classmethod
    def from_dto(cls, dto) -> "PollutantReadingResponse":
        """Create from DTO."""
        return cls(
            id=dto.id,
            station_id=dto.station_id,
            pollutant_type=dto.pollutant_type,
            value=dto.value,
            unit=dto.unit,
            quality_flag=dto.quality_flag,
            timestamp=dto.timestamp,
            created_at=dto.created_at,
        )


class StationReadingsResponse(BaseModel):
    """Station readings with multiple pollutants."""
    
    station_id: UUID
    station_name: str
    timestamp: datetime
    readings: Dict[str, float]
    source: str
    
    @classmethod
    def from_dto(cls, dto) -> "StationReadingsResponse":
        """Create from DTO."""
        return cls(
            station_id=dto.station_id,
            station_name=dto.station_name,
            timestamp=dto.timestamp,
            readings=dto.readings,
            source=dto.source,
        )


class StationReadingsListResponse(BaseModel):
    """Paginated list of readings."""
    
    items: List[PollutantReadingResponse]
    total: int
    skip: int
    limit: int
    
    @classmethod
    def from_dto(cls, dto) -> "StationReadingsListResponse":
        """Create from DTO."""
        return cls(
            items=[PollutantReadingResponse.from_dto(r) for r in dto.items],
            total=dto.total,
            skip=dto.skip,
            limit=dto.limit,
        )


class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str


class ErrorResponse(BaseModel):
    """Error response."""
    
    detail: str
    
    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "Station not found"}}
    )


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    service: str
