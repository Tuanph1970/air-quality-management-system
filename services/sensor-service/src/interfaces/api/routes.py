"""FastAPI application, lifespan management, and route registration.

This module is the entry-point referenced by ``main.py``::

    uvicorn.run("src.interfaces.api.routes:app", ...)

It creates the FastAPI application, wires up the lifespan hooks for
infrastructure resources (TimescaleDB, RabbitMQ publisher), registers
routers, and installs global exception handlers that translate domain
errors into proper HTTP responses.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ...domain.exceptions.sensor_exceptions import (
    CalibrationError,
    InvalidReadingError,
    InvalidSensorStatusError,
    SensorAlreadyExistsError,
    SensorAlreadyOnlineError,
    SensorDomainError,
    SensorNotCalibratedError,
    SensorNotFoundError,
    SensorOfflineError,
)
from ...infrastructure.persistence.timescale_database import Base, get_engine
from .dependencies import get_event_publisher, init_event_publisher
from .sensor_controller import router as sensor_router

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application lifecycle.

    **Startup**:
        1. Create database tables (safe no-op when Alembic manages schema).
        2. Initialise and connect the RabbitMQ event publisher.

    **Shutdown**:
        1. Close the RabbitMQ publisher.
        2. Dispose the SQLAlchemy engine.
    """
    # ---- startup -------------------------------------------------------
    logger.info("Sensor service starting up ...")

    # Database — create tables if they don't exist
    _engine = get_engine()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified")

    # RabbitMQ publisher
    publisher = init_event_publisher()
    try:
        await publisher.connect()
        logger.info("RabbitMQ publisher connected")
    except Exception:
        logger.warning(
            "RabbitMQ publisher connection failed — events will not be "
            "published.  The service will continue to serve HTTP requests.",
            exc_info=True,
        )

    yield

    # ---- shutdown ------------------------------------------------------
    logger.info("Sensor service shutting down ...")

    # Close publisher
    try:
        pub = get_event_publisher()
        await pub.close()
        logger.info("RabbitMQ publisher closed")
    except RuntimeError:
        pass  # publisher was never initialised

    # Dispose engine
    await get_engine().dispose()
    logger.info("Database engine disposed")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sensor Service",
    description=(
        "Microservice for managing air-quality sensors, collecting readings, "
        "and publishing events within the Air Quality Management System."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check (no auth required)
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["health"],
    summary="Service health check",
)
async def health_check():
    """Return a simple health status for load-balancer probes."""
    return {"status": "healthy", "service": "sensor-service"}


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(sensor_router)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(SensorNotFoundError)
async def sensor_not_found_handler(request: Request, exc: SensorNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


@app.exception_handler(SensorAlreadyExistsError)
async def sensor_already_exists_handler(
    request: Request, exc: SensorAlreadyExistsError,
):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail},
    )


@app.exception_handler(SensorOfflineError)
async def sensor_offline_handler(request: Request, exc: SensorOfflineError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(SensorAlreadyOnlineError)
async def sensor_already_online_handler(
    request: Request, exc: SensorAlreadyOnlineError,
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(InvalidSensorStatusError)
async def invalid_sensor_status_handler(
    request: Request, exc: InvalidSensorStatusError,
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(InvalidReadingError)
async def invalid_reading_handler(request: Request, exc: InvalidReadingError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(SensorNotCalibratedError)
async def sensor_not_calibrated_handler(
    request: Request, exc: SensorNotCalibratedError,
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(CalibrationError)
async def calibration_error_handler(request: Request, exc: CalibrationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(SensorDomainError)
async def domain_error_handler(request: Request, exc: SensorDomainError):
    logger.warning("Unhandled domain error: %s", exc.detail)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {"msg": "Validation error"}
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")
    detail = f"{field}: {message}" if field else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )
