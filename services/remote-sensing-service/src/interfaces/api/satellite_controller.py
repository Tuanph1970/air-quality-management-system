"""Satellite data API controller.

Provides endpoints for fetching, querying, and managing satellite data
from Copernicus CAMS, NASA MODIS, and Sentinel-5P TROPOMI.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.services.satellite_data_service import SatelliteDataService
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.satellite_source import SatelliteSource
from .dependencies import get_satellite_service, get_scheduler
from .schemas import (
    FetchSatelliteRequest,
    LocationDataRequest,
    LocationDataResponse,
    ManualFetchRequest,
    ManualFetchResponse,
    SatelliteDataListResponse,
    SatelliteDataResponse,
    ScheduleConfigResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/satellite", tags=["satellite"])


# ---------------------------------------------------------------------------
# Query endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/data/{data_id}",
    response_model=SatelliteDataResponse,
    summary="Get satellite data by ID",
)
async def get_satellite_data(
    data_id: str,
    service: SatelliteDataService = Depends(get_satellite_service),
):
    """Retrieve a specific satellite data record by its UUID."""
    result = await service.get_by_id(data_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Satellite data not found",
        )
    return result.to_dict()


@router.get(
    "/data/latest/{source}",
    response_model=SatelliteDataResponse,
    summary="Get latest satellite data for a source",
)
async def get_latest_data(
    source: str,
    data_type: Optional[str] = None,
    service: SatelliteDataService = Depends(get_satellite_service),
):
    """Get the most recent satellite data for a given source."""
    try:
        satellite_source = SatelliteSource(source)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown satellite source: {source}",
        )

    # Derive data_type from source if not explicitly provided.
    resolved_type = data_type or source.split("_")[-1].upper()
    result = await service.get_latest(satellite_source, resolved_type)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for this source",
        )
    return result.to_dict()


@router.get(
    "/data",
    response_model=SatelliteDataListResponse,
    summary="List satellite data with filters",
)
async def list_satellite_data(
    source: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service: SatelliteDataService = Depends(get_satellite_service),
):
    """List available satellite data with optional source and date filters."""
    if source and start_date and end_date:
        try:
            satellite_source = SatelliteSource(source)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown satellite source: {source}",
            )
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        results = await service.get_by_time_range(
            satellite_source, start_dt, end_dt
        )
        data = [r.to_dict() for r in results]
    else:
        data = []

    return {"data": data, "total": len(data)}


@router.post(
    "/data/location",
    response_model=LocationDataResponse,
    summary="Get satellite data for a location",
)
async def get_data_for_location(
    request: LocationDataRequest,
    service: SatelliteDataService = Depends(get_satellite_service),
):
    """Get all available satellite data values at a specific lat/lon."""
    sources = await service.get_data_for_location(
        request.latitude, request.longitude
    )
    return LocationDataResponse(
        latitude=request.latitude,
        longitude=request.longitude,
        sources=sources,
    )


# ---------------------------------------------------------------------------
# Fetch endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/fetch",
    response_model=SatelliteDataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger satellite data fetch",
)
async def trigger_fetch(
    request: FetchSatelliteRequest,
    service: SatelliteDataService = Depends(get_satellite_service),
):
    """Manually trigger a satellite data fetch for a specific source."""
    from ...config import settings

    # Use request bbox or fall back to the configured city bbox.
    if request.bbox:
        bbox = GeoPolygon(
            north=request.bbox.north,
            south=request.bbox.south,
            east=request.bbox.east,
            west=request.bbox.west,
        )
    else:
        bbox = GeoPolygon(
            north=settings.CITY_BBOX_NORTH,
            south=settings.CITY_BBOX_SOUTH,
            east=settings.CITY_BBOX_EAST,
            west=settings.CITY_BBOX_WEST,
        )

    target_date = request.target_date or date.today()
    source_str = request.source.value

    try:
        if "cams" in source_str:
            variable = source_str.split("_")[-1]
            result = await service.fetch_cams_data(variable, bbox, target_date)
        elif "modis" in source_str:
            use_terra = "terra" in source_str
            result = await service.fetch_modis_aod(bbox, target_date, use_terra)
        elif "tropomi" in source_str:
            pollutant = source_str.split("_")[-1].upper()
            result = await service.fetch_tropomi(pollutant, bbox, target_date)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown source: {source_str}",
            )
    except Exception as exc:
        logger.exception("Satellite fetch failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch satellite data: {exc}",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No satellite data available for the given parameters",
        )

    return result.to_dict()


@router.post(
    "/fetch/manual",
    response_model=ManualFetchResponse,
    summary="Manual scheduler fetch trigger",
)
async def manual_scheduler_fetch(request: ManualFetchRequest):
    """Trigger a manual fetch through the scheduler."""
    scheduler = get_scheduler()
    if scheduler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler is not running",
        )

    try:
        source = SatelliteSource(request.source.value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source: {request.source}",
        )

    result = await scheduler.trigger_manual_fetch(source, request.target_date)
    return ManualFetchResponse(**result)


# ---------------------------------------------------------------------------
# Scheduler config
# ---------------------------------------------------------------------------
@router.get(
    "/schedule",
    response_model=ScheduleConfigResponse,
    summary="Get fetch schedule configuration",
)
async def get_schedule():
    """Return the current scheduler configuration."""
    from ...config import settings

    return ScheduleConfigResponse(
        cams_enabled=settings.CAMS_FETCH_ENABLED,
        cams_cron=settings.CAMS_FETCH_CRON,
        modis_enabled=settings.MODIS_FETCH_ENABLED,
        modis_cron=settings.MODIS_FETCH_CRON,
        tropomi_enabled=settings.TROPOMI_FETCH_ENABLED,
        tropomi_cron=settings.TROPOMI_FETCH_CRON,
    )
