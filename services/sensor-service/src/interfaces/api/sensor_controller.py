"""Sensor API controller — HTTP endpoints for sensor and reading management.

Each endpoint maps an HTTP request to an application-layer command or query,
delegates to ``SensorApplicationService``, and returns a Pydantic response
schema.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...application.commands.calibrate_sensor_command import CalibrateSensorCommand
from ...application.commands.register_sensor_command import RegisterSensorCommand
from ...application.commands.submit_reading_command import SubmitReadingCommand
from ...application.services.sensor_application_service import (
    SensorApplicationService,
)
from ...domain.exceptions.sensor_exceptions import (
    CalibrationError,
    InvalidReadingError,
    InvalidSensorStatusError,
    SensorAlreadyExistsError,
    SensorAlreadyOnlineError,
    SensorDomainError,
    SensorNotFoundError,
    SensorOfflineError,
)
from .dependencies import get_sensor_service
from .schemas import (
    CalibrateRequest,
    ErrorResponse,
    MessageResponse,
    ReadingListResponse,
    ReadingResponse,
    ReadingSubmitRequest,
    SensorListResponse,
    SensorRegisterRequest,
    SensorResponse,
    SensorUpdateRequest,
    StatusUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sensors", tags=["sensors"])


# ---------------------------------------------------------------------------
# POST /sensors — Register a new sensor
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new sensor",
    description="Register a sensor device with its hardware details and installation location.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid payload"},
        409: {"model": ErrorResponse, "description": "Duplicate serial number"},
    },
)
async def register_sensor(
    request: SensorRegisterRequest,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> SensorResponse:
    """Register a new sensor device."""
    command = RegisterSensorCommand(
        serial_number=request.serial_number,
        sensor_type=request.sensor_type,
        model=request.model,
        latitude=request.latitude,
        longitude=request.longitude,
        factory_id=request.factory_id,
        calibration_params=request.calibration_params,
    )

    try:
        dto = await service.register_sensor(command)
    except SensorAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=exc.detail,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc),
        ) from exc

    return SensorResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# GET /sensors — List sensors (paginated, filterable)
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=SensorListResponse,
    summary="List sensors",
    description="Retrieve a paginated list of sensors with optional filters.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
    },
)
async def list_sensors(
    factory_id: Optional[UUID] = Query(
        None,
        description="Filter by factory ID",
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (ONLINE, OFFLINE, CALIBRATING, MAINTENANCE)",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    service: SensorApplicationService = Depends(get_sensor_service),
) -> SensorListResponse:
    """List all sensors with optional filtering and pagination."""
    from ...application.queries.get_sensor_query import ListSensorsQuery

    query = ListSensorsQuery(
        factory_id=factory_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    dto = await service.list_sensors(query)
    return SensorListResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# GET /sensors/{sensor_id} — Get a single sensor
# ---------------------------------------------------------------------------
@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Get sensor by ID",
    description="Retrieve detailed information about a specific sensor.",
    responses={
        404: {"model": ErrorResponse, "description": "Sensor not found"},
    },
)
async def get_sensor(
    sensor_id: UUID,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> SensorResponse:
    """Retrieve a sensor by its UUID."""
    try:
        dto = await service.get_sensor(sensor_id)
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc

    return SensorResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# PUT /sensors/{sensor_id} — Update sensor metadata
# ---------------------------------------------------------------------------
@router.put(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Update a sensor",
    description="Partially update sensor metadata.  Only non-null fields are applied.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid payload"},
        404: {"model": ErrorResponse, "description": "Sensor not found"},
    },
)
async def update_sensor(
    sensor_id: UUID,
    request: SensorUpdateRequest,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> SensorResponse:
    """Update sensor metadata (model, factory, location)."""
    try:
        # Load, apply changes via domain entity, persist
        sensor = await service._get_sensor_or_raise(sensor_id)
        sensor.update(
            model=request.model,
            factory_id=request.factory_id,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        saved = await service._sensor_repo.save(sensor)
        await service._publish_events(saved)

        from ...application.dto.sensor_dto import SensorDTO

        dto = SensorDTO.from_entity(saved)
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc),
        ) from exc

    return SensorResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# POST /sensors/{sensor_id}/readings — Submit a reading
# ---------------------------------------------------------------------------
@router.post(
    "/{sensor_id}/readings",
    response_model=ReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a sensor reading",
    description=(
        "Submit pollutant measurements from a sensor device.  "
        "The server calculates the AQI and publishes a SensorReadingCreated event."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid reading data or sensor offline"},
        404: {"model": ErrorResponse, "description": "Sensor not found"},
    },
)
async def submit_reading(
    sensor_id: UUID,
    request: ReadingSubmitRequest,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> ReadingResponse:
    """Submit a sensor reading (typically from IoT devices).

    Flow:
        1. Validate reading data.
        2. Calculate AQI using EPA algorithm.
        3. Save to TimescaleDB.
        4. Publish SensorReadingCreated event (consumed by Alert Service).
    """
    command = SubmitReadingCommand(
        sensor_id=sensor_id,
        pm25=request.pm25,
        pm10=request.pm10,
        co=request.co,
        co2=request.co2,
        no2=request.no2,
        nox=request.nox,
        so2=request.so2,
        o3=request.o3,
        temperature=request.temperature,
        humidity=request.humidity,
        timestamp=request.timestamp,
    )

    try:
        dto = await service.submit_reading(command)
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc
    except SensorOfflineError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail,
        ) from exc
    except InvalidReadingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail,
        ) from exc

    return ReadingResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# GET /sensors/{sensor_id}/readings — Get readings (with time range)
# ---------------------------------------------------------------------------
@router.get(
    "/{sensor_id}/readings",
    response_model=ReadingListResponse,
    summary="Get sensor readings",
    description="Retrieve readings for a sensor with optional time range filtering.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        404: {"model": ErrorResponse, "description": "Sensor not found"},
    },
)
async def get_readings(
    sensor_id: UUID,
    start_time: Optional[datetime] = Query(
        None,
        description="Start of time range (ISO 8601)",
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="End of time range (ISO 8601)",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    service: SensorApplicationService = Depends(get_sensor_service),
) -> ReadingListResponse:
    """Retrieve readings for a sensor with optional time range."""
    from ...application.queries.get_readings_query import GetReadingsQuery

    # Verify sensor exists
    try:
        await service.get_sensor(sensor_id)
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc

    query = GetReadingsQuery(
        sensor_id=sensor_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )
    dto = await service.get_readings(query)
    return ReadingListResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# GET /sensors/{sensor_id}/readings/latest — Get latest reading
# ---------------------------------------------------------------------------
@router.get(
    "/{sensor_id}/readings/latest",
    response_model=ReadingResponse,
    summary="Get latest reading",
    description="Retrieve the most recent reading for a sensor.",
    responses={
        404: {"model": ErrorResponse, "description": "Sensor or reading not found"},
    },
)
async def get_latest_reading(
    sensor_id: UUID,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> ReadingResponse:
    """Retrieve the most recent reading for a sensor."""
    try:
        await service.get_sensor(sensor_id)
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc

    dto = await service.get_latest_reading(sensor_id)
    if dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No readings found for sensor {sensor_id}",
        )
    return ReadingResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# POST /sensors/{sensor_id}/calibrate — Calibrate a sensor
# ---------------------------------------------------------------------------
@router.post(
    "/{sensor_id}/calibrate",
    response_model=SensorResponse,
    summary="Calibrate a sensor",
    description="Apply new calibration parameters to a sensor.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid calibration or sensor offline"},
        404: {"model": ErrorResponse, "description": "Sensor not found"},
    },
)
async def calibrate_sensor(
    sensor_id: UUID,
    request: CalibrateRequest,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> SensorResponse:
    """Apply calibration parameters to a sensor."""
    command = CalibrateSensorCommand(
        sensor_id=sensor_id,
        calibration_params=request.calibration_params,
        calibrated_by=request.calibrated_by,
    )

    try:
        dto = await service.calibrate_sensor(command)
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc
    except (InvalidSensorStatusError, CalibrationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail,
        ) from exc

    return SensorResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# PUT /sensors/{sensor_id}/status — Update sensor status
# ---------------------------------------------------------------------------
@router.put(
    "/{sensor_id}/status",
    response_model=SensorResponse,
    summary="Update sensor status",
    description="Change the operational status of a sensor.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid status transition"},
        404: {"model": ErrorResponse, "description": "Sensor not found"},
    },
)
async def update_sensor_status(
    sensor_id: UUID,
    request: StatusUpdateRequest,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> SensorResponse:
    """Update the operational status of a sensor."""
    try:
        dto = await service.update_sensor_status(
            sensor_id=sensor_id,
            new_status=request.status,
            reason=request.reason,
        )
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc
    except (
        SensorAlreadyOnlineError,
        InvalidSensorStatusError,
        SensorOfflineError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail,
        ) from exc

    return SensorResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# DELETE /sensors/{sensor_id} — Delete a sensor
# ---------------------------------------------------------------------------
@router.delete(
    "/{sensor_id}",
    response_model=MessageResponse,
    summary="Delete a sensor",
    description="Permanently remove a sensor from the system.",
    responses={
        404: {"model": ErrorResponse, "description": "Sensor not found"},
    },
)
async def delete_sensor(
    sensor_id: UUID,
    service: SensorApplicationService = Depends(get_sensor_service),
) -> MessageResponse:
    """Delete a sensor permanently."""
    try:
        await service.delete_sensor(sensor_id)
    except SensorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc

    return MessageResponse(message=f"Sensor {sensor_id} deleted successfully")
