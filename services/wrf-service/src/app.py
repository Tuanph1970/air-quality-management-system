"""FastAPI application for WRF Service."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .infrastructure.persistence.database import get_db_manager
from .interfaces.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting WRF Service...")

    # Initialize database
    try:
        db_mgr = get_db_manager(settings.DATABASE_URL)
        await db_mgr.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down WRF Service...")
    try:
        db_mgr = get_db_manager(settings.DATABASE_URL)
        await db_mgr.close()
    except Exception as e:
        logger.warning(f"Error closing database: {e}")


# Create FastAPI application
app = FastAPI(
    title="WRF Weather Forecasting Service",
    description=(
        "Service for running WRF (Weather Research and Forecasting) model simulations. "
        "Provides weather data (temperature, humidity, wind, pressure) for air quality modeling."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "port": settings.SERVICE_PORT,
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
