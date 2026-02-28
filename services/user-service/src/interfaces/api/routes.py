"""FastAPI application with lifespan management for User Service.

Creates the ``FastAPI`` app instance and wires up:
- Database connection
- RabbitMQ publisher for user events
- Graceful shutdown of all resources
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ...config import settings
from .auth_controller import router as auth_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the user service."""
    # --- Startup ---
    logger.info("Starting User Service...")

    # Database tables are created on startup (dev convenience)
    from ...infrastructure.persistence.database import Base, get_engine
    from ...infrastructure.persistence import models as _models  # noqa: F401 – register all models

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    logger.info("User Service started successfully")

    yield

    # --- Shutdown ---
    logger.info("Shutting down User Service resources...")

    # Dispose database engine
    await engine.dispose()

    logger.info("User Service shutdown complete")


app = FastAPI(
    title="User Service",
    description="User authentication and authorization service with JWT tokens.",
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
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """Liveness probe for container orchestration."""
    return {
        "status": "healthy",
        "service": "user-service",
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "User Service",
        "version": "1.0.0",
        "description": "Authentication and user management",
        "docs": "/docs",
        "health": "/health",
    }
