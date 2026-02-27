"""Data fusion and cross-validation API controller.

Provides endpoints for running data fusion, cross-validation, and
sensor calibration against satellite observations.
"""
from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.services.data_fusion_application_service import (
    DataFusionApplicationService,
)
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.satellite_source import SatelliteSource
from .dependencies import get_fusion_service
from .schemas import (
    CalibrationRequest,
    CalibrationResponse,
    CrossValidationRequest,
    CrossValidationResultResponse,
    FusionRequest,
    FusionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fusion", tags=["fusion"])


# ---------------------------------------------------------------------------
# Fusion endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/run",
    response_model=FusionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run data fusion",
)
async def run_fusion(
    request: FusionRequest,
    service: DataFusionApplicationService = Depends(get_fusion_service),
):
    """Run data fusion for the specified area, time range, and pollutant."""
    bbox = GeoPolygon(
        north=request.bbox.north,
        south=request.bbox.south,
        east=request.bbox.east,
        west=request.bbox.west,
    )
    sources = None
    if request.sources:
        sources = [SatelliteSource(s.value) for s in request.sources]

    try:
        result = await service.run_fusion(
            bbox=bbox,
            time_range=(request.start_time, request.end_time),
            pollutant=request.pollutant,
            sources=sources,
        )
    except Exception as exc:
        logger.exception("Fusion failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fusion failed: {exc}",
        )

    return result.to_dict()


@router.get(
    "/{fusion_id}",
    response_model=FusionResponse,
    summary="Get fusion result by ID",
)
async def get_fusion(
    fusion_id: UUID,
    service: DataFusionApplicationService = Depends(get_fusion_service),
):
    """Retrieve a specific fusion result by its UUID."""
    result = await service.get_fused_data(fusion_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fusion result not found",
        )
    return result.to_dict()


@router.get(
    "/latest",
    response_model=FusionResponse,
    summary="Get latest fusion result",
)
async def get_latest_fusion(
    pollutant: Optional[str] = None,
    service: DataFusionApplicationService = Depends(get_fusion_service),
):
    """Get the most recent fusion result, optionally filtered by pollutant."""
    result = await service.get_latest_fusion(pollutant or "")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fusion results found",
        )
    return result.to_dict()


# ---------------------------------------------------------------------------
# Cross-validation endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/cross-validate",
    response_model=List[CrossValidationResultResponse],
    summary="Run cross-validation",
)
async def run_cross_validation(
    request: CrossValidationRequest,
    service: DataFusionApplicationService = Depends(get_fusion_service),
):
    """Run cross-validation between sensor readings and satellite data."""
    try:
        source = SatelliteSource(request.source.value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source: {request.source}",
        )

    try:
        results = await service.run_cross_validation(
            source=source,
            start_time=request.start_time,
            end_time=request.end_time,
            pollutant=request.pollutant,
        )
    except Exception as exc:
        logger.exception("Cross-validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cross-validation failed: {exc}",
        )

    return results


# ---------------------------------------------------------------------------
# Calibration endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/calibrate",
    response_model=CalibrationResponse,
    summary="Run sensor calibration",
)
async def run_calibration(
    request: CalibrationRequest,
    service: DataFusionApplicationService = Depends(get_fusion_service),
):
    """Run sensor calibration against satellite observations."""
    try:
        source = SatelliteSource(request.source.value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source: {request.source}",
        )

    try:
        result = await service.run_calibration(
            source=source,
            start_time=request.start_time,
            end_time=request.end_time,
            sensor_id=request.sensor_id,
        )
    except Exception as exc:
        logger.exception("Calibration failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calibration failed: {exc}",
        )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"],
        )

    return result
