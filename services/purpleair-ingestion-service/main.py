"""PurpleAir Ingestion Service - Main application."""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.publisher import get_publisher
from src.api.routes import router as purpleair_router
from src.services.polling_service import get_polling_service


logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME}...")

    # Connect to RabbitMQ
    try:
        publisher = get_publisher()
        await publisher.connect()
        logger.info("RabbitMQ publisher connected")
    except Exception as e:
        logger.warning(f"RabbitMQ connection failed: {e}")

    # Start polling service if sensors are configured
    polling_service = None
    if settings.PURPLEAIR_SENSORS:
        try:
            polling_service = get_polling_service()
            await polling_service.start()
            logger.info(
                f"Polling service started with {len(settings.PURPLEAIR_SENSORS)} sensors "
                f"(interval={settings.PURPLEAIR_POLLING_INTERVAL_HOURS}h)"
            )
        except Exception as e:
            logger.warning(f"Failed to start polling service: {e}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")

    # Stop polling service
    if polling_service:
        try:
            await polling_service.stop()
            logger.info("Polling service stopped")
        except Exception as e:
            logger.warning(f"Error stopping polling service: {e}")

    try:
        publisher = get_publisher()
        await publisher.close()
    except Exception:
        pass

    logger.info("Shutdown complete")


# =============================================================================
# FastAPI application
# =============================================================================

app = FastAPI(
    title="PurpleAir Ingestion Service",
    description=(
        "Service for ingesting data from PurpleAir Flex-Air Quality Monitors. "
        "Supports webhook data push from devices and cloud API polling. "
        "Publishes events to RabbitMQ for AQI recalculation."
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

app.include_router(purpleair_router)


# =============================================================================
# Exception handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# =============================================================================
# Main entry point
# =============================================================================

def main() -> None:
    """Run the PurpleAir ingestion service."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    
    logger.info(
        "Starting %s on port %d (log_level=%s)",
        settings.SERVICE_NAME,
        settings.SERVICE_PORT,
        settings.LOG_LEVEL,
    )
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
