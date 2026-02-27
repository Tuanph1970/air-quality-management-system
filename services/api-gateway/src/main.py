"""API Gateway - Main Application Entry Point.

The API Gateway is the single entry point for all client requests.
It handles:
- Authentication (JWT verification)
- Rate limiting
- Request logging
- Routing to backend microservices
- Response aggregation for dashboard endpoints
"""
from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .middleware.auth_middleware import AuthMiddleware
from .middleware.rate_limiter import RateLimitMiddleware
from .middleware.request_logger import RequestLoggerMiddleware
from .routes import (
    air_quality_router,
    alert_router,
    auth_router,
    dashboard_router,
    factory_router,
    sensor_router,
)
from .utils.service_client import registry

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        Configured FastAPI application
    """
    app = FastAPI(
        title="AQMS API Gateway",
        description="Air Quality Management System - API Gateway. "
                    "Single entry point for all client requests with authentication, "
                    "rate limiting, and routing to backend microservices.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # =========================================================================
    # Middleware (order matters - executed in reverse order on response)
    # =========================================================================

    # 1. Request Logger - logs all requests (outermost)
    if settings.LOG_REQUESTS:
        app.add_middleware(RequestLoggerMiddleware)
        logger.info("Request logging middleware enabled")

    # 2. Rate Limiter - protects against abuse
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
        logger.info(f"Rate limiting enabled ({settings.RATE_LIMIT_DEFAULT}/min)")

    # 3. Auth Middleware - verifies JWT tokens
    app.add_middleware(AuthMiddleware)
    logger.info("Authentication middleware enabled")

    # 4. CORS - cross-origin requests
    cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS.split(",") if settings.CORS_ALLOW_METHODS != "*" else ["*"],
        allow_headers=settings.CORS_ALLOW_HEADERS.split(",") if settings.CORS_ALLOW_HEADERS != "*" else ["*"],
    )
    logger.info(f"CORS enabled for origins: {cors_origins}")

    # =========================================================================
    # Routes
    # =========================================================================

    # Health check
    @app.get("/health", tags=["health"])
    async def health_check():
        """Liveness probe for container orchestration."""
        health = {
            "status": "healthy",
            "service": "api-gateway",
            "version": "1.0.0",
        }

        # Check backend services
        services = {
            "factory-service": settings.FACTORY_SERVICE_URL,
            "sensor-service": settings.SENSOR_SERVICE_URL,
            "alert-service": settings.ALERT_SERVICE_URL,
            "air-quality-service": settings.AIR_QUALITY_SERVICE_URL,
            "user-service": settings.USER_SERVICE_URL,
        }

        for name, url in services.items():
            health[name] = "configured"

        return health

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "AQMS API Gateway",
            "version": "1.0.0",
            "description": "Air Quality Management System API",
            "documentation": "/docs",
            "health": "/health",
            "endpoints": {
                "authentication": "/api/v1/auth",
                "factories": "/api/v1/factories",
                "sensors": "/api/v1/sensors",
                "alerts": "/api/v1/alerts",
                "violations": "/api/v1/violations",
                "air-quality": "/api/v1/air-quality",
                "dashboard": "/api/v1/dashboard",
            },
        }

    # API Routes
    app.include_router(auth_router)  # Public endpoints
    app.include_router(factory_router)
    app.include_router(sensor_router)
    app.include_router(alert_router)
    app.include_router(air_quality_router)
    app.include_router(dashboard_router)  # Requires auth

    logger.info("All routes registered")

    # =========================================================================
    # Startup/Shutdown Events
    # =========================================================================

    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        logger.info("Starting API Gateway...")

        # Register service clients
        registry.register("factory-service", settings.FACTORY_SERVICE_URL)
        registry.register("sensor-service", settings.SENSOR_SERVICE_URL)
        registry.register("alert-service", settings.ALERT_SERVICE_URL)
        registry.register("air-quality-service", settings.AIR_QUALITY_SERVICE_URL)
        registry.register("user-service", settings.USER_SERVICE_URL)

        # Connect all clients
        await registry.connect_all()

        logger.info("API Gateway started successfully")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down API Gateway...")
        await registry.close_all()
        logger.info("API Gateway shutdown complete")

    # =========================================================================
    # Exception Handlers
    # =========================================================================

    @app.exception_handler(500)
    async def internal_error_handler(request, exc):
        """Handle internal server errors."""
        logger.error(f"Internal error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


# Create the application instance
app = create_app()


# For running directly with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
