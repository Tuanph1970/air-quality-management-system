"""FastAPI application with lifespan management.

Creates the ``FastAPI`` app instance and wires up:
- Database table creation on startup.
- RabbitMQ publisher and consumer connections.
- Automatic event consumer startup via ``asyncio.Task``.
- Graceful shutdown of all resources.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ...infrastructure.messaging.event_consumers import (
    AlertEventHandler,
    set_publisher,
)
from ...infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher
from ...infrastructure.persistence.database import Base, get_engine
from .alert_controller import router as alert_router

logger = logging.getLogger(__name__)

# Module-level references for shutdown cleanup.
_publisher: RabbitMQEventPublisher | None = None
_consumer = None  # shared.messaging.consumer.RabbitMQConsumer
_consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the alert service."""
    global _publisher, _consumer, _consumer_task

    # --- Startup ---

    # 1. Create database tables (dev convenience; use Alembic in prod).
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    # 2. Connect the RabbitMQ publisher.
    _publisher = RabbitMQEventPublisher()
    await _publisher.connect()

    # Inject the publisher into the event handler module so handlers
    # can publish ViolationDetected events.
    set_publisher(_publisher)

    # 3. Connect the RabbitMQ consumer and subscribe to bindings.
    from shared.messaging.config import ALERT_SERVICE_BINDINGS
    from shared.messaging.consumer import RabbitMQConsumer

    _consumer = RabbitMQConsumer()
    await _consumer.connect()

    handler = AlertEventHandler()
    await _consumer.subscribe_bindings(
        bindings=ALERT_SERVICE_BINDINGS,
        handlers=handler.get_handlers(),
    )

    # 4. Start consuming in a background task so FastAPI can serve HTTP.
    _consumer_task = asyncio.create_task(
        _consumer.start_consuming(),
        name="alert-event-consumer",
    )
    logger.info("Alert event consumer started in background")

    yield

    # --- Shutdown ---
    logger.info("Shutting down alert service resources")

    # Cancel the consumer task.
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass

    # Close the consumer connection.
    if _consumer:
        await _consumer.close()

    # Close the publisher connection.
    if _publisher:
        await _publisher.close()

    # Dispose the database engine.
    await engine.dispose()

    logger.info("Alert service shutdown complete")


app = FastAPI(
    title="Alert Service",
    description="Alerts and violations microservice — monitors sensor "
    "readings against configured thresholds and manages violations.",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routers
app.include_router(alert_router)


@app.get("/health")
async def health_check():
    """Liveness probe for container orchestration."""
    return {"status": "healthy", "service": "alert-service"}
