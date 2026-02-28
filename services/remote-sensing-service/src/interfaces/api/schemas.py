"""Pydantic request/response schemas for the remote-sensing API."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class SatelliteSourceEnum(str, Enum):
    """Satellite data sources exposed via the API."""

    MODIS_TERRA = "modis_terra"
    MODIS_AQUA = "modis_aqua"
    TROPOMI_NO2 = "tropomi_no2"
    TROPOMI_SO2 = "tropomi_so2"
    TROPOMI_O3 = "tropomi_o3"
    TROPOMI_CO = "tropomi_co"
    CAMS_PM25 = "cams_pm25"
    CAMS_PM10 = "cams_pm10"
    CAMS_FORECAST = "cams_forecast"


class ImportDataTypeEnum(str, Enum):
    """Excel import data types."""

    HISTORICAL_READINGS = "historical_readings"
    FACTORY_RECORDS = "factory_records"


# ---------------------------------------------------------------------------
# Satellite Schemas
# ---------------------------------------------------------------------------
class BoundingBoxSchema(BaseModel):
    """Geographic bounding box."""

    north: float = Field(..., ge=-90, le=90)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    west: float = Field(..., ge=-180, le=180)


class FetchSatelliteRequest(BaseModel):
    """Request body for triggering a satellite data fetch."""

    source: SatelliteSourceEnum
    bbox: Optional[BoundingBoxSchema] = None
    target_date: Optional[date] = None
    variables: Optional[List[str]] = None


class SatelliteDataResponse(BaseModel):
    """Response for a single satellite data record."""

    id: UUID
    source: str
    data_type: str
    observation_time: datetime
    fetch_time: datetime
    bbox: Dict
    grid_cell_count: int
    average_value: float
    quality_flag: str
    metadata: Dict

    class Config:
        from_attributes = True


class SatelliteDataListResponse(BaseModel):
    """Paginated list of satellite data records."""

    data: List[SatelliteDataResponse]
    total: int


class LocationDataRequest(BaseModel):
    """Request body for querying satellite data at a location."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class LocationDataResponse(BaseModel):
    """Response with satellite data values at a specific location."""

    latitude: float
    longitude: float
    sources: Dict[str, Dict]


# ---------------------------------------------------------------------------
# Fusion Schemas
# ---------------------------------------------------------------------------
class FusionRequest(BaseModel):
    """Request body for running data fusion."""

    bbox: BoundingBoxSchema
    start_time: datetime
    end_time: datetime
    pollutant: str = "PM25"
    sources: Optional[List[SatelliteSourceEnum]] = None


class FusionDataPointResponse(BaseModel):
    """Single fused data point."""

    lat: float
    lon: float
    fused_value: float
    confidence: float
    sources: List[str]
    source_values: Dict[str, float]


class FusionResponse(BaseModel):
    """Response for a data fusion result."""

    id: UUID
    sources_used: List[str]
    bbox: Dict
    time_range_start: datetime
    time_range_end: datetime
    data_point_count: int
    average_confidence: float
    pollutant: str
    created_at: datetime
    data_points: List[FusionDataPointResponse] = []
    metadata: Dict = {}

    class Config:
        from_attributes = True


class CrossValidationRequest(BaseModel):
    """Request body for cross-validation."""

    source: SatelliteSourceEnum
    start_time: datetime
    end_time: datetime
    pollutant: str = "PM25"


class CrossValidationResultResponse(BaseModel):
    """Single cross-validation result."""

    sensor_id: str
    sensor_value: float
    satellite_value: float
    deviation_percent: float
    is_anomalous: bool
    pollutant: str
    timestamp: str


class CalibrationRequest(BaseModel):
    """Request body for sensor calibration."""

    source: SatelliteSourceEnum
    start_time: datetime
    end_time: datetime
    sensor_id: Optional[UUID] = None


class CalibrationResponse(BaseModel):
    """Calibration result."""

    sensor_id: Optional[str]
    slope: float
    intercept: float
    r_squared: float
    rmse: float
    training_samples: int
    model_version: str
    computed_at: str


# ---------------------------------------------------------------------------
# Excel Import Schemas
# ---------------------------------------------------------------------------
class ExcelValidationResponse(BaseModel):
    """Excel file validation result."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    row_count: int
    columns_found: List[str]


class ExcelImportResponse(BaseModel):
    """Excel import status response."""

    id: UUID
    filename: str
    data_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    record_count: int = 0
    processed_count: int = 0
    error_count: int = 0
    errors: List[str] = []

    class Config:
        from_attributes = True


class ExcelImportListResponse(BaseModel):
    """Paginated list of import records."""

    data: List[ExcelImportResponse]
    total: int


# ---------------------------------------------------------------------------
# Scheduler Schemas
# ---------------------------------------------------------------------------
class ScheduleConfigResponse(BaseModel):
    """Current scheduler configuration."""

    cams_enabled: bool
    cams_cron: str
    modis_enabled: bool
    modis_cron: str
    tropomi_enabled: bool
    tropomi_cron: str


class ScheduleUpdateRequest(BaseModel):
    """Request body to update scheduler configuration."""

    cams_enabled: Optional[bool] = None
    cams_cron: Optional[str] = None
    modis_enabled: Optional[bool] = None
    modis_cron: Optional[str] = None
    tropomi_enabled: Optional[bool] = None
    tropomi_cron: Optional[str] = None


class ExcelTemplateResponse(BaseModel):
    """Excel template information."""

    id: str
    name: str
    description: str
    columns: List[str]
    download_url: str


class ExcelTemplateListResponse(BaseModel):
    """List of available Excel templates."""

    templates: List[ExcelTemplateResponse]


class ManualFetchRequest(BaseModel):
    """Request body to trigger a manual satellite fetch."""

    source: SatelliteSourceEnum
    target_date: Optional[date] = None


class ManualFetchResponse(BaseModel):
    """Result of a manual satellite fetch."""

    status: str
    source: str
    data_id: Optional[str] = None
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """Service health status."""

    status: str
    service: str
    scheduler_running: bool
