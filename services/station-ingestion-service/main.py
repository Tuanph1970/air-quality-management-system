"""Station Ingestion Service - Main entry point.

This service fetches data from external environmental monitoring APIs
and provides REST endpoints for the frontend.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.core.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Station Ingestion Service...")
    logger.info(f"External API URL: {config.STATION_API_BASE_URL}")

    # Initialize database tables
    from src.infrastructure.persistence.models import create_tables

    try:
        create_tables(config.DATABASE_URL)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Station Ingestion Service...")


app = FastAPI(
    title="Station Ingestion Service",
    description="Service for ingesting environmental monitoring station data",
    version="1.0.0",
    lifespan=lifespan,
)

# =========================================================================
# CORS Middleware - Enable frontend access
# =========================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Station Ingestion Service",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
    )
