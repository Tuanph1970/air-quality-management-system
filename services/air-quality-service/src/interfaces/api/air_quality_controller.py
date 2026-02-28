"""Air Quality Service API Controller.

REST API endpoints for:
- Current AQI data
- Map visualization data
- Heatmap tiles (Google API proxy)
- AQI forecasts
- Historical data
- Health recommendations
"""
from __future__ import annotations

import logging
import struct
import zlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import Response

from ...application.services.air_quality_application_service import (
    AirQualityApplicationService,
    get_air_quality_service,
)
from ...domain.value_objects.aqi_category import get_all_categories
from ...infrastructure.external.sensor_service_client import SensorServiceClient, get_sensor_service_client
from .schemas import (
    AQICategoriesResponse,
    AQICategoryInfo,
    CurrentAQIRequest,
    CurrentAQIResponse,
    ForecastRequest,
    ForecastResponse,
    HealthRecommendationResponse,
    HistoryReadingResponse,
    HistoryRequest,
    HistoryResponse,
    MapDataRequest,
    MapDataResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["air-quality"])


# =============================================================================
# Dependency Injection
# =============================================================================


def get_service() -> AirQualityApplicationService:
    """Inject the air quality application service."""
    return next(get_air_quality_service())


def get_sensor_client() -> SensorServiceClient:
    """Inject the sensor service client."""
    return next(get_sensor_service_client())


# =============================================================================
# Current AQI Endpoints
# =============================================================================


@router.get("/aqi/current", response_model=CurrentAQIResponse)
async def get_current_aqi(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(10.0, ge=1, le=100, description="Search radius in km"),
    include_pollutants: bool = Query(True, description="Include individual pollutant AQIs"),
    service: AirQualityApplicationService = Depends(get_service),
) -> CurrentAQIResponse:
    """Get current AQI for a location.

    Returns the current Air Quality Index and pollutant data for the
    specified location, aggregated from nearby sensors.
    """
    from ...application.queries.get_current_aqi_query import GetCurrentAQIQuery

    query = GetCurrentAQIQuery(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        include_pollutants=include_pollutants,
    )

    result = await service.get_current_aqi(query)
    return CurrentAQIResponse.model_validate(result)


@router.post("/aqi/current", response_model=CurrentAQIResponse)
async def get_current_aqi_post(
    request: CurrentAQIRequest,
    service: AirQualityApplicationService = Depends(get_service),
) -> CurrentAQIResponse:
    """Get current AQI for a location (POST)."""
    from ...application.queries.get_current_aqi_query import GetCurrentAQIQuery

    query = GetCurrentAQIQuery(
        latitude=request.latitude,
        longitude=request.longitude,
        radius_km=request.radius_km,
        include_pollutants=request.include_pollutants,
    )

    result = await service.get_current_aqi(query)
    return CurrentAQIResponse.model_validate(result)


# =============================================================================
# Map Data Endpoints
# =============================================================================


@router.get("/aqi/map", response_model=MapDataResponse)
async def get_map_data(
    min_lat: float = Query(..., ge=-90, le=90, description="Bounds min latitude"),
    min_lng: float = Query(..., ge=-180, le=180, description="Bounds min longitude"),
    max_lat: float = Query(..., ge=-90, le=90, description="Bounds max latitude"),
    max_lng: float = Query(..., ge=-180, le=180, description="Bounds max longitude"),
    zoom_level: int = Query(10, ge=1, le=20, description="Map zoom level"),
    include_forecast: bool = Query(False, description="Include forecast data"),
    service: AirQualityApplicationService = Depends(get_service),
) -> MapDataResponse:
    """Get aggregated AQI data for map visualization.

    Returns grid cells with AQI data suitable for rendering heatmaps.
    """
    from ...application.queries.get_map_data_query import GetMapDataQuery

    query = GetMapDataQuery(
        min_lat=min_lat,
        min_lng=min_lng,
        max_lat=max_lat,
        max_lng=max_lng,
        zoom_level=zoom_level,
        include_forecast=include_forecast,
    )

    result = await service.get_map_data(query)
    return MapDataResponse.model_validate(result)


@router.post("/aqi/map", response_model=MapDataResponse)
async def get_map_data_post(
    request: MapDataRequest,
    service: AirQualityApplicationService = Depends(get_service),
) -> MapDataResponse:
    """Get map data (POST)."""
    from ...application.queries.get_map_data_query import GetMapDataQuery

    query = GetMapDataQuery(
        min_lat=request.min_lat,
        min_lng=request.min_lng,
        max_lat=request.max_lat,
        max_lng=request.max_lng,
        zoom_level=request.zoom_level,
        include_forecast=request.include_forecast,
    )

    result = await service.get_map_data(query)
    return MapDataResponse.model_validate(result)


# =============================================================================
# Heatmap Tile Endpoint (Google API Proxy)
# =============================================================================


@router.get("/aqi/heatmap/tiles/{zoom}/{x}/{y}")
async def get_heatmap_tile(
    zoom: int = Path(..., ge=0, le=20, description="Zoom level"),
    x: int = Path(..., ge=0, description="Tile X coordinate"),
    y: int = Path(..., ge=0, description="Tile Y coordinate"),
    service: AirQualityApplicationService = Depends(get_service),
) -> Response:
    """Get air quality heatmap tile.

    Proxies requests to Google Maps Air Quality API when configured.
    Falls back to generated tiles when Google API is unavailable.

    Returns PNG image data.
    """
    from ...config import settings

    # Try Google Maps API first
    if service.google_client and service.google_client.is_configured():
        tile_data = await service.google_client.get_heatmap_tile(zoom, x, y)
        if tile_data:
            return Response(content=tile_data, media_type="image/png")

    # Fallback: Generate a placeholder tile (solid color based on zoom)
    # In production, you might want to generate actual heatmap tiles
    # using a library like matplotlib or PIL
    placeholder_color = bytes([0x00, 0xE4, 0x00, 0xFF])  # Green (Good AQI)
    tile_size = 256
    
    # Create a simple colored tile (in production, use proper image generation)
    # This is a minimal PNG placeholder
    import struct
    import zlib
    
    def create_minimal_png(color: bytes, size: int = 256) -> bytes:
        """Create a minimal solid-color PNG."""
        # PNG signature
        signature = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        
        # IDAT chunk (compressed image data)
        raw_data = b''
        for y in range(size):
            raw_data += b'\x00'  # Filter byte
            for x in range(size):
                raw_data += color[:3]  # RGB
        
        compressed = zlib.compress(raw_data)
        idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
        idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
        
        # IEND chunk
        iend_crc = zlib.crc32(b'IEND') & 0xffffffff
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        
        return signature + ihdr + idat + iend
    
    tile_png = create_minimal_png(placeholder_color, tile_size)
    return Response(content=tile_png, media_type="image/png")


# =============================================================================
# Forecast Endpoints
# =============================================================================


@router.get("/aqi/forecast", response_model=ForecastResponse)
async def get_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    hours: int = Query(24, ge=1, le=168, description="Forecast duration (hours)"),
    interval_hours: int = Query(1, ge=1, le=24, description="Data point interval"),
    service: AirQualityApplicationService = Depends(get_service),
) -> ForecastResponse:
    """Get AQI forecast for a location."""
    from ...application.queries.get_forecast_query import GetForecastQuery

    query = GetForecastQuery(
        latitude=latitude,
        longitude=longitude,
        hours=hours,
        interval_hours=interval_hours,
    )

    result = await service.get_forecast(query)
    return ForecastResponse.model_validate(result)


@router.post("/aqi/forecast", response_model=ForecastResponse)
async def get_forecast_post(
    request: ForecastRequest,
    service: AirQualityApplicationService = Depends(get_service),
) -> ForecastResponse:
    """Get forecast (POST)."""
    from ...application.queries.get_forecast_query import GetForecastQuery

    query = GetForecastQuery(
        latitude=request.latitude,
        longitude=request.longitude,
        hours=request.hours,
        interval_hours=request.interval_hours,
    )

    result = await service.get_forecast(query)
    return ForecastResponse.model_validate(result)


# =============================================================================
# Historical Data Endpoints
# =============================================================================


@router.get("/aqi/history", response_model=HistoryResponse)
async def get_history(
    sensor_id: str = Query(..., min_length=1, description="Sensor identifier"),
    start: datetime = Query(..., description="Start timestamp (ISO format)"),
    end: datetime = Query(..., description="End timestamp (ISO format)"),
    limit: int = Query(1000, ge=1, le=10000, description="Max readings to return"),
    sensor_client: SensorServiceClient = Depends(get_sensor_client),
    service: AirQualityApplicationService = Depends(get_service),
) -> HistoryResponse:
    """Get historical AQI data for a sensor.

    Fetches historical readings from the Sensor Service and calculates
    summary statistics.
    """
    # Fetch readings from Sensor Service
    readings = await sensor_client.get_sensor_readings(sensor_id, start, end, limit)

    if not readings:
        return HistoryResponse(
            sensor_id=sensor_id,
            start=start,
            end=end,
            readings=[],
            total=0,
            average_aqi=0,
            min_aqi=0,
            max_aqi=0,
        )

    # Convert to response format
    reading_responses = [
        HistoryReadingResponse(
            sensor_id=r.sensor_id,
            factory_id=r.factory_id,
            latitude=r.latitude,
            longitude=r.longitude,
            aqi_value=r.aqi,
            pm25=r.pm25 if r.pm25 > 0 else None,
            pm10=r.pm10 if r.pm10 > 0 else None,
            co=r.co if r.co > 0 else None,
            no2=r.no2 if r.no2 > 0 else None,
            so2=r.so2 if r.so2 > 0 else None,
            o3=r.o3 if r.o3 > 0 else None,
            timestamp=r.timestamp,
        )
        for r in readings
    ]

    # Calculate statistics
    aqi_values = [r.aqi for r in readings]
    
    return HistoryResponse(
        sensor_id=sensor_id,
        start=start,
        end=end,
        readings=reading_responses,
        total=len(readings),
        average_aqi=round(sum(aqi_values) / len(aqi_values)),
        min_aqi=min(aqi_values),
        max_aqi=max(aqi_values),
    )


@router.post("/aqi/history", response_model=HistoryResponse)
async def get_history_post(
    request: HistoryRequest,
    sensor_client: SensorServiceClient = Depends(get_sensor_client),
    service: AirQualityApplicationService = Depends(get_service),
) -> HistoryResponse:
    """Get historical data (POST)."""
    return await get_history(
        sensor_id=request.sensor_id,
        start=request.start,
        end=request.end,
        limit=request.limit,
        sensor_client=sensor_client,
        service=service,
    )


# =============================================================================
# Health & Information Endpoints
# =============================================================================


@router.get("/aqi/categories", response_model=AQICategoriesResponse)
async def get_aqi_categories() -> AQICategoriesResponse:
    """Get all AQI categories with health information."""
    categories = get_all_categories()
    return AQICategoriesResponse(
        categories=[
            AQICategoryInfo(
                level=cat.level.value,
                min_aqi=cat.min_aqi,
                max_aqi=cat.max_aqi,
                color_hex=cat.color_hex,
                color_name=cat.color_name,
                health_message=cat.health_message,
                caution_message=cat.caution_message,
            )
            for cat in categories
        ]
    )


@router.get("/aqi/health", response_model=HealthRecommendationResponse)
async def get_health_recommendation(
    aqi: int = Query(..., ge=0, le=500, description="AQI value"),
) -> HealthRecommendationResponse:
    """Get health recommendations for an AQI value."""
    from ...domain.value_objects.aqi_category import get_category_for_aqi

    category = get_category_for_aqi(aqi)

    sensitive_groups = []
    outdoor_guidance = ""

    if aqi <= 50:
        outdoor_guidance = "Ideal conditions for outdoor activities."
    elif aqi <= 100:
        sensitive_groups = ["Unusually sensitive individuals"]
        outdoor_guidance = "Acceptable for most outdoor activities."
    elif aqi <= 150:
        sensitive_groups = [
            "People with heart or lung disease",
            "Older adults",
            "Children",
        ]
        outdoor_guidance = "Sensitive groups should reduce prolonged outdoor exertion."
    elif aqi <= 200:
        sensitive_groups = [
            "People with heart or lung disease",
            "Older adults",
            "Children",
            "General public",
        ]
        outdoor_guidance = "Everyone should reduce prolonged outdoor exertion."
    elif aqi <= 300:
        sensitive_groups = ["Everyone"]
        outdoor_guidance = "Avoid prolonged or heavy outdoor exertion."
    else:
        sensitive_groups = ["Everyone"]
        outdoor_guidance = "Avoid all physical activity outdoors."

    return HealthRecommendationResponse(
        aqi_value=aqi,
        level=category.level.value,
        health_message=category.health_message,
        caution_message=category.caution_message,
        sensitive_groups=sensitive_groups,
        outdoor_activity_guidance=outdoor_guidance,
    )
