"""Station API controller - HTTP request handlers."""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .schemas import (
    StationCreateRequest,
    StationUpdateRequest,
    StationAPIConfigureRequest,
    StationRecordReadingsRequest,
    StationResponse,
    StationListResponse,
    StationReadingsResponse,
    StationReadingsListResponse,
    PollutantReadingResponse,
    MessageResponse,
)
from ...application.commands import (
    CreateStationCommand,
    UpdateStationCommand,
    ConfigureStationAPICommand,
    ActivateStationCommand,
    DeactivateStationCommand,
    RecordStationReadingsCommand,
    DeleteStationCommand,
)
from ...application.queries import (
    GetStationQuery,
    GetStationByCodeQuery,
    ListStationsQuery,
    GetNearbyStationsQuery,
    GetStationReadingsQuery,
    GetLatestStationReadingsQuery,
)
from ...application.services import StationApplicationService
from ...domain.exceptions.station_exceptions import (
    StationNotFoundError,
    StationAlreadyExistsError,
    InvalidStationConfigurationError,
    StationDataValidationError,
    StationAlreadyActiveError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stations", tags=["stations"])


# Dependency injection
def get_application_service() -> StationApplicationService:
    """Get application service instance."""
    from .dependencies import get_station_app_service
    return get_station_app_service()


# =============================================================================
# Station Management Endpoints
# =============================================================================

@router.post(
    "",
    response_model=StationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new station",
)
async def create_station(
    request: StationCreateRequest,
    service: StationApplicationService = Depends(get_application_service),
):
    """Create a new air quality monitoring station.
    
    - **name**: Human-readable station name
    - **station_code**: Unique external identifier (e.g., EPA station ID)
    - **station_type**: Classification (GOVERNMENT, INDUSTRIAL, URBAN, RURAL, TRAFFIC, BACKGROUND)
    - **latitude/longitude**: GPS coordinates
    - **altitude**: Optional altitude in meters
    """
    command = CreateStationCommand(
        name=request.name,
        station_code=request.station_code,
        station_type=request.station_type,
        latitude=request.latitude,
        longitude=request.longitude,
        altitude=request.altitude,
        data_retention_days=request.data_retention_days,
        metadata=request.metadata,
    )
    
    try:
        dto = await service.create_station(command)
        return StationResponse.from_dto(dto)
    except StationAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidStationConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=StationListResponse,
    summary="List all stations",
)
async def list_stations(
    station_type: Optional[str] = Query(None, description="Filter by station type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum to return"),
    service: StationApplicationService = Depends(get_application_service),
):
    """List stations with optional filters."""
    query = ListStationsQuery(
        station_type=station_type,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    
    dto = await service.list_stations(query)
    return StationListResponse.from_dto(dto)


@router.get(
    "/{station_id}",
    response_model=StationResponse,
    summary="Get station by ID",
)
async def get_station(
    station_id: UUID,
    service: StationApplicationService = Depends(get_application_service),
):
    """Get details of a specific station."""
    query = GetStationQuery(station_id=station_id)
    
    try:
        dto = await service.get_station(query)
        return StationResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/code/{station_code}",
    response_model=StationResponse,
    summary="Get station by external code",
)
async def get_station_by_code(
    station_code: str,
    service: StationApplicationService = Depends(get_application_service),
):
    """Get station by external code (e.g., EPA station ID)."""
    query = GetStationByCodeQuery(station_code=station_code)
    
    try:
        dto = await service.get_station_by_code(query)
        return StationResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/{station_id}",
    response_model=StationResponse,
    summary="Update station",
)
async def update_station(
    station_id: UUID,
    request: StationUpdateRequest,
    service: StationApplicationService = Depends(get_application_service),
):
    """Update station properties."""
    command = UpdateStationCommand(
        station_id=station_id,
        name=request.name,
        station_type=request.station_type,
        latitude=request.latitude,
        longitude=request.longitude,
        altitude=request.altitude,
        metadata=request.metadata,
        data_retention_days=request.data_retention_days,
    )
    
    try:
        dto = await service.update_station(command)
        return StationResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStationConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{station_id}",
    response_model=MessageResponse,
    summary="Delete station",
)
async def delete_station(
    station_id: UUID,
    service: StationApplicationService = Depends(get_application_service),
):
    """Delete a station."""
    command = DeleteStationCommand(station_id=station_id)
    
    try:
        await service.delete_station(command)
        return MessageResponse(message="Station deleted successfully")
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Station API Configuration Endpoints
# =============================================================================

@router.post(
    "/{station_id}/configure-api",
    response_model=StationResponse,
    summary="Configure station API endpoint",
)
async def configure_station_api(
    station_id: UUID,
    request: StationAPIConfigureRequest,
    service: StationApplicationService = Depends(get_application_service),
):
    """Configure API endpoint for automatic data collection.
    
    - **endpoint**: API URL to fetch data from
    - **method**: HTTP method (GET, POST, etc.)
    - **auth_type**: Authentication type (none, basic, bearer, api_key)
    - **adapter_type**: Adapter type (generic, epa, etc.)
    - **poll_interval_seconds**: How often to poll (minimum 10 seconds)
    """
    command = ConfigureStationAPICommand(
        station_id=station_id,
        endpoint=request.endpoint,
        method=request.method,
        headers=request.headers,
        auth_type=request.auth_type,
        auth_credentials=request.auth_credentials,
        poll_interval_seconds=request.poll_interval_seconds,
        adapter_type=request.adapter_type,
        request_template=request.request_template,
        response_mapping=request.response_mapping,
    )
    
    try:
        dto = await service.configure_station_api(command)
        return StationResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStationConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{station_id}/activate",
    response_model=StationResponse,
    summary="Activate station",
)
async def activate_station(
    station_id: UUID,
    service: StationApplicationService = Depends(get_application_service),
):
    """Activate a station for data collection."""
    command = ActivateStationCommand(station_id=station_id)
    
    try:
        dto = await service.activate_station(command)
        return StationResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StationAlreadyActiveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidStationConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{station_id}/deactivate",
    response_model=StationResponse,
    summary="Deactivate station",
)
async def deactivate_station(
    station_id: UUID,
    reason: str = Query("", description="Reason for deactivation"),
    service: StationApplicationService = Depends(get_application_service),
):
    """Deactivate a station."""
    command = DeactivateStationCommand(station_id=station_id, reason=reason)
    
    try:
        dto = await service.deactivate_station(command)
        return StationResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Station Data Endpoints
# =============================================================================

@router.post(
    "/{station_id}/record-readings",
    response_model=StationReadingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record station readings",
)
async def record_station_readings(
    station_id: UUID,
    request: StationRecordReadingsRequest,
    service: StationApplicationService = Depends(get_application_service),
):
    """Record readings from a station (webhook or manual entry).
    
    This endpoint is used to:
    - Receive webhook data from external stations
    - Manually enter readings
    - Test data ingestion
    
    - **readings**: Dictionary of pollutant_name -> value
    - **timestamp**: Optional ISO 8601 timestamp
    - **source**: Data source (API, WEBHOOK, MANUAL)
    """
    command = RecordStationReadingsCommand(
        station_id=station_id,
        readings=request.readings,
        timestamp=request.timestamp,
        source=request.source,
        metadata=request.metadata,
    )
    
    try:
        dto = await service.record_station_readings(command)
        return StationReadingsResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StationDataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{station_id}/readings",
    response_model=StationReadingsListResponse,
    summary="Get station readings",
)
async def get_station_readings(
    station_id: UUID,
    start_time: Optional[str] = Query(None, description="Filter readings after this time (ISO 8601)"),
    end_time: Optional[str] = Query(None, description="Filter readings before this time (ISO 8601)"),
    pollutant_type: Optional[str] = Query(None, description="Filter by pollutant type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: StationApplicationService = Depends(get_application_service),
):
    """Get historical readings for a station."""
    query = GetStationReadingsQuery(
        station_id=station_id,
        start_time=start_time,
        end_time=end_time,
        pollutant_type=pollutant_type,
        skip=skip,
        limit=limit,
    )
    
    try:
        dto = await service.get_station_readings(query)
        return StationReadingsListResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{station_id}/readings/latest",
    response_model=StationReadingsResponse,
    summary="Get latest station readings",
)
async def get_latest_station_readings(
    station_id: UUID,
    service: StationApplicationService = Depends(get_application_service),
):
    """Get the most recent readings from a station."""
    query = GetLatestStationReadingsQuery(station_id=station_id)
    
    try:
        dto = await service.get_latest_station_readings(query)
        return StationReadingsResponse.from_dto(dto)
    except StationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get(
    "/nearby",
    response_model=StationListResponse,
    summary="Find nearby stations",
)
async def find_nearby_stations(
    latitude: float = Query(..., ge=-90, le=90, description="Center latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_km: float = Query(10.0, gt=0, le=1000, description="Search radius in kilometers"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    service: StationApplicationService = Depends(get_application_service),
):
    """Find stations near a geographic location."""
    query = GetNearbyStationsQuery(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit,
    )
    
    dto = await service.get_nearby_stations(query)
    return StationListResponse.from_dto(dto)
