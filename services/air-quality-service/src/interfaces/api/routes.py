"""FastAPI application with lifespan management for Air Quality Service.

Creates the ``FastAPI`` app instance and wires up:
- Redis cache connection on startup
- Google Maps client initialization
- RabbitMQ consumer for sensor events
- Graceful shutdown of all resources
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ...config import settings
from ...infrastructure.cache.redis_cache import RedisCache
from ...infrastructure.external.google_maps_client import GoogleMapsClient
from .air_quality_controller import router as air_quality_router

logger = logging.getLogger(__name__)

# Module-level references for shutdown cleanup.
_cache: RedisCache | None = None
_google_client: GoogleMapsClient | None = None
_consumer = None  # shared.messaging.consumer.RabbitMQConsumer
_consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the air quality service."""
    global _cache, _google_client, _consumer, _consumer_task

    # --- Startup ---
    logger.info("Starting Air Quality Service...")

    # 1. Initialize Redis cache
    _cache = RedisCache()
    await _cache.connect()

    # 2. Initialize Google Maps client
    _google_client = GoogleMapsClient()
    await _google_client.connect()

    # 3. Connect RabbitMQ consumer for sensor events (optional)
    # The service listens to SensorReadingCreated events to update cache
    try:
        from shared.messaging.config import AIR_QUALITY_SERVICE_BINDINGS
        from shared.messaging.consumer import RabbitMQConsumer

        _consumer = RabbitMQConsumer()
        await _consumer.connect()

        # Import and set up event handler
        from ...infrastructure.messaging.event_consumers import (
            AirQualityEventHandler,
            set_cache_for_handler,
        )

        set_cache_for_handler(_cache)

        handler = AirQualityEventHandler()
        await _consumer.subscribe_bindings(
            bindings=AIR_QUALITY_SERVICE_BINDINGS,
            handlers=handler.get_handlers(),
        )

        # Start consuming in background
        _consumer_task = asyncio.create_task(
            _consumer.start_consuming(),
            name="aq-event-consumer",
        )
        logger.info("Air Quality event consumer started")

    except Exception as e:
        logger.warning(f"Could not start RabbitMQ consumer: {e}")

    logger.info("Air Quality Service started successfully")

    yield

    # --- Shutdown ---
    logger.info("Shutting down Air Quality Service resources...")

    # Cancel consumer task
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass

    # Close consumer connection
    if _consumer:
        await _consumer.close()

    # Close Google Maps client
    if _google_client:
        await _google_client.close()

    # Close Redis cache
    if _cache:
        await _cache.close()

    logger.info("Air Quality Service shutdown complete")


app = FastAPI(
    title="Air Quality Service",
    description="Air Quality Index (AQI) calculation, forecasting, and map visualization service.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(air_quality_router)


@app.get("/health")
async def health_check():
    """Liveness probe for container orchestration."""
    health = {
        "status": "healthy",
        "service": "air-quality-service",
    }

    # Check Redis health
    if _cache:
        redis_healthy = await _cache.is_available()
        health["redis"] = "connected" if redis_healthy else "disconnected"

    # Check Google Maps API
    if _google_client:
        health["google_maps"] = "configured" if _google_client.is_configured() else "not configured"

    return health


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Air Quality Service",
        "version": "1.0.0",
        "description": "AQI calculation, forecasting, and map visualization",
        "docs": "/docs",
        "health": "/health",
    }
