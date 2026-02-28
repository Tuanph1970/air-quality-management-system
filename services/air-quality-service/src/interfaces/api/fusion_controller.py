"""Data Fusion, Cross-Validation, and Calibration API Controller.

REST API endpoints for:
- Fused air quality data (sensor + satellite)
- Cross-validation reports and per-sensor validation
- Calibration model status, metrics, and retraining
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ...application.services.air_quality_application_service import (
    AirQualityApplicationService,
)
from .dependencies import get_air_quality_service
from .schemas import (
    CalibrationMetricsResponse,
    CalibrationStatusResponse,
    FusedDataListResponse,
    TrainCalibrationRequest,
    TrainingResultResponse,
    ValidationReportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/air-quality", tags=["data-fusion"])


# =========================================================================
# Fused Data Endpoints
# =========================================================================


@router.get("/fused", response_model=FusedDataListResponse)
async def get_fused_data(
    lat_min: float = Query(..., ge=-90, le=90, description="South latitude"),
    lat_max: float = Query(..., ge=-90, le=90, description="North latitude"),
    lon_min: float = Query(..., ge=-180, le=180, description="West longitude"),
    lon_max: float = Query(..., ge=-180, le=180, description="East longitude"),
    timestamp: Optional[datetime] = Query(
        default=None, description="Observation timestamp (defaults to now)"
    ),
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Get fused air quality data for a bounding box.

    Returns sensor + satellite fused data points with calibrated PM2.5/PM10,
    AQI values, and confidence scores.
    """
    bbox = {
        "north": lat_max,
        "south": lat_min,
        "east": lon_max,
        "west": lon_min,
    }
    data = await service.get_fused_data(bbox, timestamp)
    return FusedDataListResponse(data=data, total=len(data))


@router.post("/fuse")
async def trigger_fusion(
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Manually trigger data fusion for the current time.

    Fetches recent sensor readings and cached satellite data, runs
    calibration, and stores the fused results in cache.
    """
    result = await service.trigger_fusion()
    return {"message": "Fusion triggered", "points_fused": result}


@router.get("/fused/map")
async def get_fused_map_data(
    lat_min: float = Query(..., ge=-90, le=90, description="South latitude"),
    lat_max: float = Query(..., ge=-90, le=90, description="North latitude"),
    lon_min: float = Query(..., ge=-180, le=180, description="West longitude"),
    lon_max: float = Query(..., ge=-180, le=180, description="East longitude"),
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Get fused data formatted for map visualization.

    Returns grid cells with fused AQI, confidence, and contributing sources,
    suitable for rendering heatmaps on the frontend.
    """
    bbox = {
        "north": lat_max,
        "south": lat_min,
        "east": lon_max,
        "west": lon_min,
    }
    return await service.get_fused_map_data(bbox)


# =========================================================================
# Cross-Validation Endpoints
# =========================================================================


@router.get("/validation/report", response_model=ValidationReportResponse)
async def get_validation_report(
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Get cross-validation report for all sensors.

    Compares recent sensor readings against satellite reference data and
    returns per-sensor correlation, bias, RMSE, and pass/fail status.
    """
    return await service.get_validation_report()


@router.get("/validation/sensors/{sensor_id}")
async def get_sensor_validation(
    sensor_id: UUID,
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Get validation status for a specific sensor.

    Returns detailed cross-validation metrics between the sensor and
    satellite reference data.
    """
    result = await service.get_sensor_validation(sensor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return result


@router.post("/validation/run")
async def run_validation(
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Trigger cross-validation for all active sensors.

    Fetches recent sensor and satellite data, runs the cross-validation
    service, and caches the results.
    """
    result = await service.run_validation()
    return {"message": "Validation completed", "sensors_validated": result}


# =========================================================================
# Calibration Endpoints
# =========================================================================


@router.get("/calibration/status", response_model=CalibrationStatusResponse)
async def get_calibration_status(
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Get calibration model status.

    Returns whether a trained model exists, its feature set, and
    last training time.
    """
    return await service.get_calibration_status()


@router.get("/calibration/metrics", response_model=CalibrationMetricsResponse)
async def get_calibration_metrics(
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Get calibration model performance metrics.

    Returns R-squared, RMSE, MAE, bias, and feature importance from the
    most recent model evaluation.
    """
    return await service.get_calibration_metrics()


@router.post("/calibration/train", response_model=TrainingResultResponse)
async def train_calibration_model(
    request: TrainCalibrationRequest,
    service: AirQualityApplicationService = Depends(get_air_quality_service),
):
    """Retrain calibration model with recent data.

    Collects matched sensor-satellite pairs from the specified time window
    and retrains the GradientBoosting calibration model.
    """
    result = await service.retrain_calibration(
        days=request.training_days,
        min_samples=request.min_samples,
    )
    return result
