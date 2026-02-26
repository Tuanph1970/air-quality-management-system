"""FastAPI application, lifespan management, and route registration.

This module is the entry-point referenced by ``main.py``::

    uvicorn.run("src.interfaces.api.routes:app", ...)

It creates the FastAPI application, wires up the lifespan hooks for
infrastructure resources (RabbitMQ publisher, event consumers, database),
registers routers, and installs global exception handlers that translate
domain errors into proper HTTP responses.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ...domain.exceptions.factory_exceptions import (
    FactoryAlreadyExistsError,
    FactoryAlreadySuspendedError,
    FactoryClosedError,
    FactoryDomainError,
    FactoryNotFoundError,
    FactoryNotSuspendedError,
    InvalidFactoryStatusError,
)
from ...infrastructure.persistence.database import Base, get_engine
from .dependencies import get_event_publisher, init_event_publisher
from .factory_controller import router as factory_router

logger = logging.getLogger(__name__)

# Module-level reference so shutdown can cancel the consumer task.
_consumer_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# Event consumer bootstrap
# ---------------------------------------------------------------------------
async def _start_event_consumers() -> None:
    """Connect a ``RabbitMQConsumer`` and subscribe to factory-relevant queues.

    Runs as a background ``asyncio.Task`` so the HTTP server keeps
    serving while the consumer processes inbound events.
    """
    try:
        from shared.messaging.config import FACTORY_SERVICE_BINDINGS
        from shared.messaging.consumer import RabbitMQConsumer

        from ...infrastructure.messaging.event_handlers import FactoryEventHandler

        consumer = RabbitMQConsumer()
        await consumer.connect()

        handler = FactoryEventHandler()
        await consumer.subscribe_bindings(
            bindings=FACTORY_SERVICE_BINDINGS,
            handlers=handler.get_handlers(),
        )
        logger.info("Event consumers started — listening for inbound events")

        # Block until the consumer is closed.
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

    **Shutdown**:
        1. Cancel the event consumer task.
        2. Close the RabbitMQ publisher.
        3. Dispose the SQLAlchemy engine.
    """
    global _consumer_task

    # ---- startup -------------------------------------------------------
    logger.info("Factory service starting up …")

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
        name="factory-event-consumers",
    )

    yield

    # ---- shutdown ------------------------------------------------------
    logger.info("Factory service shutting down …")

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
        pass  # publisher was never initialised

    # Dispose engine
    await get_engine().dispose()
    logger.info("Database engine disposed")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Factory Service",
    description=(
        "Microservice for managing factories, their emission limits, "
        "and operational status within the Air Quality Management System."
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
    return {"status": "healthy", "service": "factory-service"}


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(factory_router)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(FactoryNotFoundError)
async def factory_not_found_handler(request: Request, exc: FactoryNotFoundError):
    """Map ``FactoryNotFoundError`` → 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


@app.exception_handler(FactoryAlreadyExistsError)
async def factory_already_exists_handler(
    request: Request, exc: FactoryAlreadyExistsError,
):
    """Map ``FactoryAlreadyExistsError`` → 409."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail},
    )


@app.exception_handler(FactoryAlreadySuspendedError)
async def factory_already_suspended_handler(
    request: Request, exc: FactoryAlreadySuspendedError,
):
    """Map ``FactoryAlreadySuspendedError`` → 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(FactoryNotSuspendedError)
async def factory_not_suspended_handler(
    request: Request, exc: FactoryNotSuspendedError,
):
    """Map ``FactoryNotSuspendedError`` → 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(FactoryClosedError)
async def factory_closed_handler(request: Request, exc: FactoryClosedError):
    """Map ``FactoryClosedError`` → 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(InvalidFactoryStatusError)
async def invalid_status_handler(
    request: Request, exc: InvalidFactoryStatusError,
):
    """Map ``InvalidFactoryStatusError`` → 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(FactoryDomainError)
async def domain_error_handler(request: Request, exc: FactoryDomainError):
    """Catch-all for any unhandled domain error → 400."""
    logger.warning("Unhandled domain error: %s", exc.detail)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Override default 422 handler for consistent error shape."""
    errors = exc.errors()
    first_error = errors[0] if errors else {"msg": "Validation error"}
    field = " → ".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")
    detail = f"{field}: {message}" if field else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Map bare ``ValueError`` from command validation → 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )
