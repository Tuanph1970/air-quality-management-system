"""Pydantic request/response schemas."""
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class AQIResponse(BaseModel):
    aqi_value: int
    level: str
    pollutants: Dict
    latitude: float
    longitude: float
    timestamp: datetime


class ForecastResponse(BaseModel):
    forecasts: List[AQIResponse]


class MapDataPoint(BaseModel):
    latitude: float
    longitude: float
    aqi_value: int
    level: str


class MapDataResponse(BaseModel):
    data: List[MapDataPoint]
    center_lat: float
    center_lng: float
    radius_km: float
