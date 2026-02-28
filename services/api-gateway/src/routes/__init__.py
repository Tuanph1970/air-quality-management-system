"""API Gateway routes."""
from .air_quality_routes import router as air_quality_router
from .alert_routes import router as alert_router
from .auth_routes import router as auth_router
from .dashboard_routes import router as dashboard_router
from .factory_routes import router as factory_router
from .satellite_routes import router as satellite_router
from .sensor_routes import router as sensor_router

__all__ = [
    "air_quality_router",
    "alert_router",
    "auth_router",
    "dashboard_router",
    "factory_router",
    "satellite_router",
    "sensor_router",
]
