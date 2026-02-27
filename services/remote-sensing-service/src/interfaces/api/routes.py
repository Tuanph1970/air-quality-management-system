"""FastAPI application, lifespan management, and route registration.

This module is the entry-point referenced by ``main.py``::

    uvicorn.run("src.interfaces.api.routes:app", ...)

It creates the FastAPI application, wires up the lifespan hooks for
infrastructure resources (RabbitMQ publisher, event consumers, database,
scheduler), registers routers, and installs global exception handlers.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ...config import settings
from ...infrastructure.persistence.database import Base, get_engine
from ...infrastructure.scheduler.satellite_scheduler import SatelliteScheduler
from .dependencies import (
    get_event_publisher,
    get_satellite_service,
    init_event_publisher,
    set_scheduler,
)
from .excel_controller import router as excel_router
from .fusion_controller import router as fusion_router
from .satellite_controller import router as satellite_router

logger = logging.getLogger(__name__)

# Module-level references for shutdown.
_consumer_task: asyncio.Task | None = None
_scheduler: SatelliteScheduler | None = None


# ---------------------------------------------------------------------------
# Event consumer bootstrap
# ---------------------------------------------------------------------------
async def _start_event_consumers() -> None:
    """Connect a ``RabbitMQConsumer`` and subscribe to remote-sensing queues."""
    try:
        from shared.messaging.config import REMOTE_SENSING_SERVICE_BINDINGS
        from shared.messaging.consumer import RabbitMQConsumer

        from ...infrastructure.messaging.event_consumers import (
            RemoteSensingEventHandler,
        )

        consumer = RabbitMQConsumer()
        await consumer.connect()

        handler = RemoteSensingEventHandler()
        await consumer.subscribe_bindings(
            bindings=REMOTE_SENSING_SERVICE_BINDINGS,
            handlers=handler.get_handlers(),
        )
        logger.info("Event consumers started — listening for inbound events")

        await consumer.start_consuming()
    except asyncio.CancelledError:
        logger.info("Event consumer task cancelled — shutting down")
    except Exception:
        logger.warning(
            "Event consumer failed — inbound events will not be processed. "
            "The service will continue to serve HTTP requests.",
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application lifecycle.

    **Startup**:
        1. Create database tables (safe no-op when Alembic manages schema).
        2. Initialise and connect the RabbitMQ event publisher.
        3. Start event consumer as a background task.
        4. Start the satellite data fetch scheduler.

    **Shutdown**:
        1. Stop the satellite scheduler.
        2. Cancel the event consumer task.
        3. Close the RabbitMQ publisher.
        4. Dispose the SQLAlchemy engine.
    """
    global _consumer_task, _scheduler

    # ---- startup -------------------------------------------------------
    logger.info("Remote Sensing Service starting up …")

    # Database
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

    # Event consumers (background task)
    _consumer_task = asyncio.create_task(
        _start_event_consumers(),
        name="remote-sensing-event-consumers",
    )

    # Satellite data fetch scheduler
    try:
        # Build a lightweight satellite service for the scheduler.
        # Uses a fresh DB session for each scheduled job.
        satellite_service = await get_satellite_service()
        _scheduler = SatelliteScheduler(satellite_service)
        _scheduler.start()
        set_scheduler(_scheduler)
        logger.info("Satellite fetch scheduler started")
    except Exception:
        logger.warning(
            "Satellite scheduler failed to start — scheduled fetches "
            "will not run.  Manual fetch endpoints remain available.",
            exc_info=True,
        )

    yield

    # ---- shutdown ------------------------------------------------------
    logger.info("Remote Sensing Service shutting down …")

    # Stop scheduler
    if _scheduler:
        _scheduler.stop()
        logger.info("Satellite scheduler stopped")

    # Cancel consumer task
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
        logger.info("Event consumer task stopped")

    # Close publisher
    try:
        pub = get_event_publisher()
        await pub.close()
        logger.info("RabbitMQ publisher closed")
    except RuntimeError:
        pass

    # Dispose engine
    await get_engine().dispose()
    logger.info("Database engine disposed")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Remote Sensing Service",
    description=(
        "Microservice for satellite data ingestion, Excel data import, "
        "data fusion, cross-validation, and sensor calibration within "
        "the Air Quality Management System."
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
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check (no auth required)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"], summary="Service health check")
async def health_check():
    """Return service health status for load-balancer probes."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "scheduler_running": _scheduler is not None,
    }


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(satellite_router)
app.include_router(excel_router)
app.include_router(fusion_router)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
):
    """Override default 422 handler for consistent error shape."""
    errors = exc.errors()
    first_error = errors[0] if errors else {"msg": "Validation error"}
    field_path = " → ".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")
    detail = f"{field_path}: {message}" if field_path else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Map bare ``ValueError`` → 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )
