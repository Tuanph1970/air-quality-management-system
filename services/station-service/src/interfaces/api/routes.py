"""FastAPI application routes and setup."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ...config import settings
from ...domain.exceptions.station_exceptions import (
    StationDomainError,
    StationNotFoundError,
    StationAlreadyExistsError,
    InvalidStationConfigurationError,
    StationAPIConfigurationError,
    InvalidPollutantReadingError,
    StationDataValidationError,
    StationOfflineError,
    StationAlreadyActiveError,
)
from ...infrastructure.persistence.database import (
    init_database,
    dispose_database,
)
from ...infrastructure.messaging import init_event_publisher
from .station_controller import router as station_router

logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}...")
    
    # Initialize database (creates tables automatically)
    try:
        await init_database()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Initialize RabbitMQ publisher
    try:
        publisher = init_event_publisher()
        await publisher.connect()
        logger.info("RabbitMQ publisher connected")
    except Exception as e:
        logger.warning(f"RabbitMQ connection failed, events will not be published: {e}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
    
    # Close RabbitMQ
    try:
        from ...infrastructure.messaging import get_event_publisher
        publisher = get_event_publisher()
        await publisher.close()
    except RuntimeError:
        pass  # Not initialized
    
    # Dispose database
    await dispose_database()
    logger.info("Shutdown complete")


# =============================================================================
# FastAPI application
# =============================================================================

app = FastAPI(
    title="Station Service",
    description=(
        "Air Quality Station Management Service - Manages air quality monitoring "
        "stations, configures API endpoints for data collection, and ingests "
        "pollutant readings (SO2, NOX, CO, PM25, PM10, O3)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# =============================================================================
# Middleware
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"{request.method} {request.url.path} - {response.status_code}")
    return response


# =============================================================================
# Health check
# =============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
    }


# =============================================================================
# Routers
# =============================================================================

app.include_router(station_router)


# =============================================================================
# Exception handlers
# =============================================================================

@app.exception_handler(StationNotFoundError)
async def station_not_found_handler(request: Request, exc: StationNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(StationAlreadyExistsError)
async def station_already_exists_handler(request: Request, exc: StationAlreadyExistsError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidStationConfigurationError)
async def invalid_config_handler(request: Request, exc: InvalidStationConfigurationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(StationAPIConfigurationError)
async def api_config_error_handler(request: Request, exc: StationAPIConfigurationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(StationDataValidationError)
async def validation_error_handler(request: Request, exc: StationDataValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(StationAlreadyActiveError)
async def already_active_handler(request: Request, exc: StationAlreadyActiveError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(StationOfflineError)
async def offline_error_handler(request: Request, exc: StationOfflineError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidPollutantReadingError)
async def invalid_reading_handler(request: Request, exc: InvalidPollutantReadingError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(StationDomainError)
async def domain_error_handler(request: Request, exc: StationDomainError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )
