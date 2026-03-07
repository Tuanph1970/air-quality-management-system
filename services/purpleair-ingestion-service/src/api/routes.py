"""PurpleAir webhook and API routes."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.publisher import get_publisher
from ..core.events import PurpleAirDataIngested, PurpleAirSensorRegistered
from ..external.fake_data_generator import generate_fake_sensor_readings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["purpleair"])


# =============================================================================
# Request/Response Schemas
# =============================================================================

class PurpleAirWebhookRequest(BaseModel):
    """PurpleAir webhook payload.
    
    PurpleAir devices send data in this format:
    {
        "sensor_id": 12345,
        "api_key": "your-api-key",
        "latitude": 21.0285,
        "longitude": 105.8542,
        "data": {
            "pm2_5": 35.5,
            "pm10_0": 50.0,
            "pm1_0": 25.0,
            "temperature": 28.5,
            "humidity": 65.0,
            "pressure": 1013.25,
            "ozone": 0.05,
            "no2": 0.03,
            "co": 0.5
        }
    }
    """
    
    sensor_id: int = Field(..., description="PurpleAir sensor ID")
    api_key: str = Field(..., description="Device API key")
    latitude: float = Field(..., ge=-90, le=90, description="Sensor latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Sensor longitude")
    data: Dict[str, float] = Field(..., description="Sensor readings")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sensor_id": 12345,
                "api_key": "your-api-key",
                "latitude": 21.0285,
                "longitude": 105.8542,
                "data": {
                    "pm2_5": 35.5,
                    "pm10_0": 50.0,
                    "pm1_0": 25.0,
                    "temperature": 28.5,
                    "humidity": 65.0,
                    "pressure": 1013.25,
                    "ozone": 0.05,
                    "no2": 0.03,
                    "co": 0.5,
                },
            }
        }
    }


class PurpleAirResponse(BaseModel):
    """Response for PurpleAir data ingestion."""
    
    success: bool
    message: str
    sensor_id: Optional[int] = None
    internal_sensor_id: Optional[str] = None


class FakeDataResponse(BaseModel):
    """Response for fake data endpoint."""
    
    success: bool
    count: int
    readings: List[Dict[str, Any]]


# =============================================================================
# Webhook Endpoint
# =============================================================================

@router.post(
    "/api/v1/purpleair/webhook",
    response_model=PurpleAirResponse,
    summary="PurpleAir webhook endpoint",
    description="Receive data from PurpleAir Flex-Air devices",
)
async def purpleair_webhook(request: PurpleAirWebhookRequest):
    """Webhook endpoint for PurpleAir devices to push data.
    
    Configure your PurpleAir device to send POST requests to this endpoint.
    The device will automatically push readings at configured intervals.
    
    **Device Configuration:**
    1. Go to your PurpleAir device page
    2. Click "Settings" → "Thingspeak"
    3. Enter your custom webhook URL
    4. Set data format to JSON
    
    **Accepted Fields:**
    - `pm2_5`: PM2.5 concentration (µg/m³)
    - `pm10_0`: PM10 concentration (µg/m³)
    - `pm1_0`: PM1.0 concentration (µg/m³)
    - `temperature`: Temperature (°C)
    - `humidity`: Relative humidity (%)
    - `pressure`: Atmospheric pressure (hPa)
    - `ozone`: Ozone concentration (ppm)
    - `no2`: Nitrogen dioxide (ppm)
    - `co`: Carbon monoxide (ppm)
    """
    try:
        # Generate internal sensor ID (mapping PurpleAir sensor to internal system)
        internal_sensor_id = f"purpleair-{request.sensor_id}"
        
        # Map PurpleAir readings to standard format
        readings = map_purpleair_readings(request.data)
        
        # Create event
        event = PurpleAirDataIngested(
            event_id=None,  # Auto-generated
            sensor_id=UUID(int=hash(internal_sensor_id) & (2**128 - 1)),  # Deterministic UUID
            purpleair_sensor_id=request.sensor_id,
            readings=readings,
            timestamp=datetime.utcnow(),
            latitude=request.latitude,
            longitude=request.longitude,
        )
        
        # Publish event
        publisher = get_publisher()
        await publisher.publish(event)
        
        logger.info(
            f"Ingested PurpleAir data from sensor {request.sensor_id}: "
            f"PM2.5={readings.get('PM25', 'N/A')}, PM10={readings.get('PM10', 'N/A')}"
        )
        
        return PurpleAirResponse(
            success=True,
            message="Data ingested successfully",
            sensor_id=request.sensor_id,
            internal_sensor_id=internal_sensor_id,
        )
        
    except Exception as e:
        logger.error(f"Error processing PurpleAir webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post(
    "/api/v1/purpleair/register",
    response_model=PurpleAirResponse,
    summary="Register a PurpleAir sensor",
    description="Register a PurpleAir sensor in the system",
)
async def register_purpleair_sensor(
    sensor_id: int,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    api_key: str = Query(...),
):
    """Register a PurpleAir sensor.
    
    This creates a mapping between the PurpleAir sensor ID and
    an internal sensor entity in the sensor-service.
    """
    try:
        internal_sensor_id = f"purpleair-{sensor_id}"
        
        # Create registration event
        event = PurpleAirSensorRegistered(
            event_id=None,
            sensor_id=UUID(int=hash(internal_sensor_id) & (2**128 - 1)),
            purpleair_sensor_id=sensor_id,
            latitude=latitude,
            longitude=longitude,
        )
        
        # Publish event
        publisher = get_publisher()
        await publisher.publish(event)
        
        logger.info(f"Registered PurpleAir sensor {sensor_id} at ({latitude}, {longitude})")
        
        return PurpleAirResponse(
            success=True,
            message="Sensor registered successfully",
            sensor_id=sensor_id,
            internal_sensor_id=internal_sensor_id,
        )
        
    except Exception as e:
        logger.error(f"Error registering sensor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


@router.get(
    "/api/v1/purpleair/fake-data",
    response_model=FakeDataResponse,
    summary="Generate fake PurpleAir data",
    description="Generate realistic fake data for demonstration",
)
async def generate_fake_data(count: int = Query(5, ge=1, le=20)):
    """Generate fake PurpleAir sensor readings for demonstration.
    
    This endpoint creates realistic-looking data that mimics
    actual PurpleAir Flex-Air monitor readings.
    """
    readings = generate_fake_sensor_readings(count)
    
    # Ingest each reading
    publisher = get_publisher()
    
    for reading in readings:
        try:
            event = PurpleAirDataIngested(
                event_id=None,
                sensor_id=UUID(int=hash(f"purpleair-{reading['sensor_id']}") & (2**128 - 1)),
                purpleair_sensor_id=reading["sensor_id"],
                readings=map_purpleair_readings(reading["data"]),
                timestamp=datetime.utcnow(),
                latitude=reading["latitude"],
                longitude=reading["longitude"],
            )
            await publisher.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish fake data event: {e}")
    
    return FakeDataResponse(
        success=True,
        count=len(readings),
        readings=readings,
    )


# =============================================================================
# Helper Functions
# =============================================================================

def map_purpleair_readings(purpleair_data: Dict[str, float]) -> Dict[str, float]:
    """Map PurpleAir readings to standard AQMS format.
    
    Args:
        purpleair_data: Raw PurpleAir sensor data
        
    Returns:
        Standardized readings dictionary
    """
    readings = {}
    
    # Map particulate matter
    if "pm2_5" in purpleair_data:
        readings["PM25"] = purpleair_data["pm2_5"]
    if "pm10_0" in purpleair_data:
        readings["PM10"] = purpleair_data["pm10_0"]
    if "pm1_0" in purpleair_data:
        readings["PM1"] = purpleair_data["pm1_0"]
    
    # Map gases (convert ppm to standard units if needed)
    if "ozone" in purpleair_data:
        # Convert ppm to µg/m³ (approximate at STP: 1 ppm O3 ≈ 2000 µg/m³)
        readings["O3"] = purpleair_data["ozone"] * 2000
    if "no2" in purpleair_data:
        # Convert ppm to µg/m³ (1 ppm NO2 ≈ 1880 µg/m³)
        readings["NO2"] = purpleair_data["no2"] * 1880
    if "co" in purpleair_data:
        # Convert ppm to mg/m³ (1 ppm CO ≈ 1.145 mg/m³)
        readings["CO"] = purpleair_data["co"] * 1.145
    
    # Map environmental (keep as-is for reference)
    if "temperature" in purpleair_data:
        readings["temperature"] = purpleair_data["temperature"]
    if "humidity" in purpleair_data:
        readings["humidity"] = purpleair_data["humidity"]
    if "pressure" in purpleair_data:
        readings["pressure"] = purpleair_data["pressure"]
    
    return readings
