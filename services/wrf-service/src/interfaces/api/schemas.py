"""Pydantic schemas for WRF Service API."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WRFSimulationCreateSchema(BaseModel):
    """Schema for creating a WRF simulation."""

    name: str = Field(..., min_length=1, max_length=255)
    north: float = Field(..., ge=-90, le=90)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    west: float = Field(..., ge=-180, le=180)
    horizontal_resolution_km: float = Field(..., ge=1, le=50)
    vertical_levels: int = Field(..., ge=10, le=100)
    simulation_hours: int = Field(..., ge=1, le=168)
    output_interval_hours: int = Field(default=1, ge=1, le=24)
    start_date: Optional[str] = None
    microphysics: str = Field(default="wsmd6")
    longwave_radiation: str = Field(default="rrtm")
    shortwave_radiation: str = Field(default="dudhia")
    land_surface: str = Field(default="noah")
    pbl_scheme: str = Field(default="ysu")


class WRFSimulationResponseSchema(BaseModel):
    """Schema for WRF simulation response."""

    id: str
    name: str
    status: str
    progress_percent: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None


class WRFSimulationDetailSchema(BaseModel):
    """Detailed schema for WRF simulation."""

    id: str
    name: str
    status: str
    progress_percent: int
    error_message: Optional[str] = None
    config: Dict[str, Any]
    output_file_path: Optional[str] = None
    wrf_output_files: List[str] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None


class WRFSimulationListSchema(BaseModel):
    """Schema for list of simulations."""

    simulations: List[WRFSimulationResponseSchema]
    total: int
    skip: int
    limit: int


class WRFStatusSchema(BaseModel):
    """Schema for simulation status."""

    id: str
    name: str
    status: str
    progress_percent: int
    error_message: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class WRFRecommendedConfigSchema(BaseModel):
    """Schema for recommended configuration."""

    config: Dict[str, Any]
    estimated_runtime_hours: float
    recommendation: str


class WRFForecastDataSchema(BaseModel):
    """Schema for forecast data."""

    simulation_id: str
    variable: str
    level: str
    bounding_box: Dict[str, Any]
    time_range: Dict[str, Optional[str]]
    output_files: List[str]


class APIResponseSchema(BaseModel):
    """Generic API response schema."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
