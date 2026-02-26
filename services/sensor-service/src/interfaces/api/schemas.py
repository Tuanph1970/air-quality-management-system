"""Pydantic request/response schemas."""
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class SensorCreateRequest(BaseModel):
    factory_id: UUID
    sensor_type: str
    latitude: float
    longitude: float


class ReadingSubmitRequest(BaseModel):
    sensor_id: UUID
    pm25: float = 0.0
    pm10: float = 0.0
    co: float = 0.0
    no2: float = 0.0
    so2: float = 0.0
    o3: float = 0.0


class CalibrateRequest(BaseModel):
    offset: float
    scale_factor: float
    calibrated_by: UUID


class SensorResponse(BaseModel):
    id: UUID
    factory_id: UUID
    sensor_type: str
    latitude: float
    longitude: float
    status: str
    last_calibration: Optional[datetime] = None


class ReadingResponse(BaseModel):
    id: UUID
    sensor_id: UUID
    pm25: float
    pm10: float
    co: float
    no2: float
    so2: float
    o3: float
    aqi: int
    timestamp: datetime


class ReadingListResponse(BaseModel):
    data: List[ReadingResponse]
    total: int
