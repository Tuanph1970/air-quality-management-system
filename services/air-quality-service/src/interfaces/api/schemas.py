"""Pydantic schemas for Air Quality Service API."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Current AQI Schemas
# =============================================================================


class CurrentAQIResponse(BaseModel):
    """Response schema for current AQI data."""

    location_lat: float = Field(..., description="Location latitude")
    location_lng: float = Field(..., description="Location longitude")
    aqi_value: int = Field(..., ge=0, le=500, description="AQI value (0-500)")
    level: str = Field(..., description="AQI level category")
    category: str = Field(..., description="Human-readable category")
    color: str = Field(..., description="Hex color code")
    dominant_pollutant: str = Field(..., description="Primary pollutant")
    pollutants: Dict = Field(default_factory=dict, description="Pollutant data")
    health_message: str = Field("", description="Health impact message")
    caution_message: str = Field("", description="Caution statement")
    timestamp: str = Field("", description="Reading timestamp")
    data_source: str = Field("sensor", description="Data source")

    model_config = {"from_attributes": True}


class CurrentAQIRequest(BaseModel):
    """Request schema for current AQI."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=10.0, ge=1, le=100)
    include_pollutants: bool = Field(default=True)


# =============================================================================
# Map Data Schemas
# =============================================================================


class MapGridCellResponse(BaseModel):
    """Response schema for a map grid cell."""

    lat: float = Field(..., description="Cell center latitude")
    lng: float = Field(..., description="Cell center longitude")
    aqi_value: int = Field(..., ge=0, le=500, description="AQI value")
    level: str = Field(..., description="AQI level")
    color: str = Field(..., description="Hex color code")
    sensor_count: int = Field(default=0, description="Contributing sensors")
    last_updated: str = Field(default="", description="Last update time")
    forecast_aqi: Optional[int] = Field(default=None, description="Forecast AQI")

    model_config = {"from_attributes": True}


class MapDataResponse(BaseModel):
    """Response schema for map data."""

    grid_cells: List[MapGridCellResponse] = Field(
        default_factory=list, description="Grid cells"
    )
    min_lat: float = Field(..., description="Bounds min latitude")
    min_lng: float = Field(..., description="Bounds min longitude")
    max_lat: float = Field(..., description="Bounds max latitude")
    max_lng: float = Field(..., description="Bounds max longitude")
    zoom_level: int = Field(..., description="Map zoom level")
    generated_at: str = Field(..., description="Generation timestamp")

    model_config = {"from_attributes": True}


class MapDataRequest(BaseModel):
    """Request schema for map data."""

    min_lat: float = Field(..., ge=-90, le=90)
    min_lng: float = Field(..., ge=-180, le=180)
    max_lat: float = Field(..., ge=-90, le=90)
    max_lng: float = Field(..., ge=-180, le=180)
    zoom_level: int = Field(default=10, ge=1, le=20)
    include_forecast: bool = Field(default=False)


# =============================================================================
# Forecast Schemas
# =============================================================================


class ForecastDataPointResponse(BaseModel):
    """Response schema for a forecast data point."""

    timestamp: datetime = Field(..., description="Forecast time")
    predicted_aqi: int = Field(..., ge=0, le=500, description="Predicted AQI")
    min_aqi: int = Field(..., ge=0, le=500, description="Lower confidence bound")
    max_aqi: int = Field(..., ge=0, le=500, description="Upper confidence bound")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level")
    trend: str = Field(..., description="Trend direction")
    level: str = Field(..., description="AQI level")

    model_config = {"from_attributes": True}


class ForecastResponse(BaseModel):
    """Response schema for AQI forecast."""

    location_lat: float = Field(..., description="Location latitude")
    location_lng: float = Field(..., description="Location longitude")
    generated_at: datetime = Field(..., description="Forecast generation time")
    forecast_hours: int = Field(..., description="Forecast duration")
    current_aqi: int = Field(default=0, description="Current AQI")
    data_points: List[ForecastDataPointResponse] = Field(
        default_factory=list, description="Forecast points"
    )
    average_aqi: int = Field(default=0, description="Average predicted AQI")
    max_aqi: int = Field(default=0, description="Maximum predicted AQI")
    overall_trend: str = Field(default="STABLE", description="Overall trend")
    health_recommendation: str = Field(default="", description="Health advice")
    summary: Dict = Field(default_factory=dict, description="Forecast summary")

    model_config = {"from_attributes": True}


class ForecastRequest(BaseModel):
    """Request schema for forecast."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    hours: int = Field(default=24, ge=1, le=168)  # Max 1 week
    interval_hours: int = Field(default=1, ge=1, le=24)


# =============================================================================
# Health & Info Schemas
# =============================================================================


class AQICategoryInfo(BaseModel):
    """Information about an AQI category."""

    level: str
    min_aqi: int
    max_aqi: int
    color_hex: str
    color_name: str
    health_message: str
    caution_message: str


class AQICategoriesResponse(BaseModel):
    """Response with all AQI categories."""

    categories: List[AQICategoryInfo] = Field(
        default_factory=list, description="All AQI categories"
    )


class HealthRecommendationResponse(BaseModel):
    """Health recommendation based on AQI."""

    aqi_value: int
    level: str
    health_message: str
    caution_message: str
    sensitive_groups: List[str] = Field(
        default_factory=list, description="Affected sensitive groups"
    )
    outdoor_activity_guidance: str = Field(
        default="", description="Activity recommendations"
    )


# =============================================================================
# History Schemas
# =============================================================================


class HistoryReadingResponse(BaseModel):
    """Response schema for a historical reading."""

    sensor_id: str = Field(..., description="Sensor identifier")
    factory_id: str = Field(..., description="Factory identifier")
    latitude: float = Field(..., description="Sensor latitude")
    longitude: float = Field(..., description="Sensor longitude")
    aqi_value: int = Field(..., ge=0, le=500, description="AQI value")
    pm25: Optional[float] = Field(default=None, description="PM2.5 concentration")
    pm10: Optional[float] = Field(default=None, description="PM10 concentration")
    co: Optional[float] = Field(default=None, description="CO concentration")
    no2: Optional[float] = Field(default=None, description="NO2 concentration")
    so2: Optional[float] = Field(default=None, description="SO2 concentration")
    o3: Optional[float] = Field(default=None, description="O3 concentration")
    timestamp: datetime = Field(..., description="Reading timestamp")

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    """Response schema for historical AQI data."""

    sensor_id: str = Field(..., description="Sensor identifier")
    start: datetime = Field(..., description="Start timestamp")
    end: datetime = Field(..., description="End timestamp")
    readings: List[HistoryReadingResponse] = Field(
        default_factory=list, description="Historical readings"
    )
    total: int = Field(..., description="Total number of readings")
    average_aqi: int = Field(default=0, description="Average AQI")
    min_aqi: int = Field(default=0, description="Minimum AQI")
    max_aqi: int = Field(default=0, description="Maximum AQI")

    model_config = {"from_attributes": True}


class HistoryRequest(BaseModel):
    """Request schema for historical data."""

    sensor_id: str = Field(..., min_length=1, description="Sensor identifier")
    start: datetime = Field(..., description="Start timestamp")
    end: datetime = Field(..., description="End timestamp")
    limit: int = Field(default=1000, ge=1, le=10000, description="Max readings")


# =============================================================================
# Fused Data Schemas
# =============================================================================


class FusedDataPointResponse(BaseModel):
    """Response schema for a single fused data point."""

    latitude: float = Field(..., description="Location latitude")
    longitude: float = Field(..., description="Location longitude")
    timestamp: datetime = Field(..., description="Observation timestamp")
    sensor_pm25: Optional[float] = Field(default=None, description="Raw sensor PM2.5")
    sensor_pm10: Optional[float] = Field(default=None, description="Raw sensor PM10")
    satellite_aod: Optional[float] = Field(default=None, description="Satellite AOD value")
    fused_pm25: Optional[float] = Field(default=None, description="Calibrated PM2.5")
    fused_pm10: Optional[float] = Field(default=None, description="Calibrated PM10")
    fused_aqi: Optional[int] = Field(default=None, description="Fused AQI value")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Data confidence score")
    data_sources: List[str] = Field(default_factory=list, description="Contributing sources")

    model_config = {"from_attributes": True}


class FusedDataResponse(BaseModel):
    """Response schema for fused data."""

    data: List[FusedDataPointResponse] = Field(default_factory=list)
    total: int = Field(default=0, description="Total fused points")
    average_confidence: float = Field(default=0.0, description="Mean confidence score")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class FusedDataListResponse(BaseModel):
    """Paginated response for fused data queries."""

    data: List[FusedDataPointResponse] = Field(default_factory=list)
    total: int = Field(default=0, description="Total fused points")

    model_config = {"from_attributes": True}


# =============================================================================
# Validation Schemas
# =============================================================================


class SensorValidationResult(BaseModel):
    """Validation result for a single sensor."""

    sensor_id: str = Field(..., description="Sensor identifier")
    sample_count: int = Field(default=0, description="Number of comparison samples")
    correlation: float = Field(default=0.0, description="Pearson correlation coefficient")
    bias: float = Field(default=0.0, description="Mean bias (sensor - satellite)")
    rmse: float = Field(default=0.0, description="Root Mean Square Error")
    mae: float = Field(default=0.0, description="Mean Absolute Error")
    is_valid: bool = Field(default=False, description="Whether sensor passes validation")
    status: str = Field(default="unknown", description="Qualitative assessment")

    model_config = {"from_attributes": True}


class ValidationReportResponse(BaseModel):
    """Response schema for cross-validation report."""

    total_sensors: int = Field(default=0, description="Total sensors evaluated")
    valid_sensors: int = Field(default=0, description="Sensors passing validation")
    invalid_sensors: int = Field(default=0, description="Sensors failing validation")
    average_correlation: float = Field(default=0.0, description="Mean correlation")
    average_bias: float = Field(default=0.0, description="Mean bias")
    sensors: List[SensorValidationResult] = Field(
        default_factory=list, description="Per-sensor validation results"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# =============================================================================
# Calibration Schemas
# =============================================================================


class CalibrationStatusResponse(BaseModel):
    """Response schema for calibration model status."""

    is_trained: bool = Field(default=False, description="Whether model is trained")
    model_path: str = Field(default="", description="Path to model file")
    feature_names: List[str] = Field(default_factory=list, description="Model features")
    last_trained: Optional[datetime] = Field(default=None, description="Last training time")

    model_config = {"from_attributes": True}


class CalibrationMetricsResponse(BaseModel):
    """Response schema for calibration model metrics."""

    r_squared: float = Field(default=0.0, description="R-squared score")
    rmse: float = Field(default=0.0, description="Root Mean Square Error")
    mae: float = Field(default=0.0, description="Mean Absolute Error")
    bias: float = Field(default=0.0, description="Mean bias")
    feature_importance: Dict = Field(
        default_factory=dict, description="Feature importance scores"
    )

    model_config = {"from_attributes": True}


class TrainCalibrationRequest(BaseModel):
    """Request schema for retraining calibration model."""

    training_days: int = Field(
        default=30, ge=7, le=365, description="Days of training data to use"
    )
    min_samples: int = Field(
        default=50, ge=50, le=10000, description="Minimum training samples required"
    )


class TrainingResultResponse(BaseModel):
    """Response schema for calibration training result."""

    model_version: str = Field(..., description="Model version identifier")
    r_squared: float = Field(..., description="Training R-squared")
    rmse: float = Field(..., description="Training RMSE")
    mae: float = Field(..., description="Training MAE")
    training_samples: int = Field(..., description="Number of training samples")
    feature_importance: Dict = Field(
        default_factory=dict, description="Feature importance scores"
    )

    model_config = {"from_attributes": True}
