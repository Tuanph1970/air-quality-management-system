"""Pydantic request/response schemas for the sensor API.

These schemas handle HTTP serialisation, validation, and OpenAPI
documentation.  They are the *only* layer that uses Pydantic — the
domain and application layers use plain dataclasses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# Request schemas
# =========================================================================

class SensorRegisterRequest(BaseModel):
    """Payload for registering a new sensor."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "serial_number": "SN-2024-001",
                "sensor_type": "LOW_COST_PM",
                "model": "PMS5003",
                "latitude": 21.0285,
                "longitude": 105.8542,
                "factory_id": "550e8400-e29b-41d4-a716-446655440000",
                "calibration_params": {},
            }
        }
    )

    serial_number: str = Field(
        ..., min_length=1, max_length=100,
        description="Unique hardware serial number",
    )
    sensor_type: str = Field(
        ..., min_length=1, max_length=50,
        description="Sensor classification (LOW_COST_PM, REFERENCE_STATION, MULTI_GAS)",
    )
    model: str = Field(
        ..., min_length=1, max_length=100,
        description="Hardware model name (e.g. PMS5003)",
    )
    latitude: float = Field(
        ..., ge=-90, le=90,
        description="Installation GPS latitude in decimal degrees",
    )
    longitude: float = Field(
        ..., ge=-180, le=180,
        description="Installation GPS longitude in decimal degrees",
    )
    factory_id: Optional[UUID] = Field(
        None,
        description="Optional factory this sensor is associated with",
    )
    calibration_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional initial calibration parameters",
    )


class SensorUpdateRequest(BaseModel):
    """Payload for partially updating a sensor.  Only non-null fields are applied."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "PMS7003",
                "latitude": 21.0300,
            }
        }
    )

    model: Optional[str] = Field(
        None, min_length=1, max_length=100,
        description="Updated hardware model",
    )
    factory_id: Optional[UUID] = Field(
        None,
        description="Updated factory association",
    )
    latitude: Optional[float] = Field(
        None, ge=-90, le=90,
        description="Updated GPS latitude",
    )
    longitude: Optional[float] = Field(
        None, ge=-180, le=180,
        description="Updated GPS longitude",
    )


class ReadingSubmitRequest(BaseModel):
    """Payload for submitting a sensor reading (typically from IoT devices).

    All pollutant values are optional and default to 0.0 — IoT devices
    send only the pollutants their hardware can measure.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pm25": 35.5,
                "pm10": 50.0,
                "co": 5.2,
                "no2": 30.0,
                "so2": 10.0,
                "o3": 60.0,
                "temperature": 28.5,
                "humidity": 65.0,
            }
        }
    )

    pm25: float = Field(0.0, ge=0, description="PM2.5 concentration (µg/m³)")
    pm10: float = Field(0.0, ge=0, description="PM10 concentration (µg/m³)")
    co: float = Field(0.0, ge=0, description="CO concentration (mg/m³)")
    co2: float = Field(0.0, ge=0, description="CO2 concentration (ppm)")
    no2: float = Field(0.0, ge=0, description="NO2 concentration (µg/m³)")
    nox: float = Field(0.0, ge=0, description="NOx concentration (µg/m³)")
    so2: float = Field(0.0, ge=0, description="SO2 concentration (µg/m³)")
    o3: float = Field(0.0, ge=0, description="O3 concentration (µg/m³)")
    temperature: float = Field(0.0, description="Temperature (°C)")
    humidity: float = Field(0.0, ge=0, le=100, description="Relative humidity (%)")
    timestamp: Optional[datetime] = Field(
        None,
        description="Measurement timestamp (defaults to server time if omitted)",
    )


class CalibrateRequest(BaseModel):
    """Payload for calibrating a sensor."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "calibration_params": {
                    "offset": 0.5,
                    "scale_factor": 1.02,
                },
                "calibrated_by": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    )

    calibration_params: Dict[str, Any] = Field(
        ...,
        description="Calibration parameters (offset, scale_factor, per-pollutant params)",
    )
    calibrated_by: Optional[UUID] = Field(
        None,
        description="User ID of the technician performing calibration",
    )


class StatusUpdateRequest(BaseModel):
    """Payload for updating sensor status."""

    status: str = Field(
        ..., min_length=1, max_length=20,
        description="New status (ONLINE, OFFLINE, MAINTENANCE)",
    )
    reason: str = Field(
        "",
        max_length=500,
        description="Optional reason for the status change",
    )


# =========================================================================
# Response schemas
# =========================================================================

class SensorResponse(BaseModel):
    """Single sensor resource."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    serial_number: str
    sensor_type: str
    model: str
    factory_id: Optional[UUID] = None
    latitude: float
    longitude: float
    status: str
    last_calibration: Optional[datetime] = None
    installation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto) -> SensorResponse:
        """Map a ``SensorDTO`` to a response schema."""
        return cls(
            id=dto.id,
            serial_number=dto.serial_number,
            sensor_type=dto.sensor_type,
            model=dto.model,
            factory_id=dto.factory_id,
            latitude=dto.latitude,
            longitude=dto.longitude,
            status=dto.status,
            last_calibration=dto.last_calibration,
            installation_date=dto.installation_date,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class SensorListResponse(BaseModel):
    """Paginated list of sensors."""

    items: List[SensorResponse]
    total: int
    skip: int
    limit: int

    @classmethod
    def from_dto(cls, dto) -> SensorListResponse:
        """Map a ``SensorListDTO`` to a response schema."""
        return cls(
            items=[SensorResponse.from_dto(s) for s in dto.items],
            total=dto.total,
            skip=dto.skip,
            limit=dto.limit,
        )


class ReadingResponse(BaseModel):
    """Single reading resource."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sensor_id: UUID
    factory_id: Optional[UUID] = None
    pm25: float
    pm10: float
    co: float
    co2: float
    no2: float
    nox: float
    so2: float
    o3: float
    temperature: float
    humidity: float
    aqi: int
    timestamp: datetime

    @classmethod
    def from_dto(cls, dto) -> ReadingResponse:
        """Map a ``ReadingDTO`` to a response schema."""
        return cls(
            id=dto.id,
            sensor_id=dto.sensor_id,
            factory_id=dto.factory_id,
            pm25=dto.pm25,
            pm10=dto.pm10,
            co=dto.co,
            co2=dto.co2,
            no2=dto.no2,
            nox=dto.nox,
            so2=dto.so2,
            o3=dto.o3,
            temperature=dto.temperature,
            humidity=dto.humidity,
            aqi=dto.aqi,
            timestamp=dto.timestamp,
        )


class ReadingListResponse(BaseModel):
    """Paginated list of readings."""

    items: List[ReadingResponse]
    total: int
    skip: int
    limit: int

    @classmethod
    def from_dto(cls, dto) -> ReadingListResponse:
        """Map a ``ReadingListDTO`` to a response schema."""
        return cls(
            items=[ReadingResponse.from_dto(r) for r in dto.items],
            total=dto.total,
            skip=dto.skip,
            limit=dto.limit,
        )


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all error handlers."""

    detail: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "Sensor not found: <id>"}}
    )


class MessageResponse(BaseModel):
    """Simple success/info message."""

    message: str
