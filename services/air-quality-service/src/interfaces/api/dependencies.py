"""FastAPI dependency injection for Air Quality Service.

Provides factory functions for injecting services into API endpoints.
Uses module-level singletons initialized during the application lifespan.
"""
from __future__ import annotations

import logging
from typing import Optional

from ...domain.services.aqi_calculator import AQICalculator
from ...domain.services.calibration_model import CalibrationModel
from ...domain.services.cross_validator import CrossValidationService
from ...domain.services.data_fusion import DataFusionService
from ...domain.services.prediction_service import PredictionService
from ...infrastructure.cache.redis_cache import RedisCache
from ...infrastructure.external.google_maps_client import GoogleMapsClient
from ...infrastructure.external.sensor_service_client import SensorServiceClient

logger = logging.getLogger(__name__)

# Module-level singletons — set by lifespan startup in routes.py.
_cache: Optional[RedisCache] = None
_google_client: Optional[GoogleMapsClient] = None
_sensor_client: Optional[SensorServiceClient] = None
_calibration_model: Optional[CalibrationModel] = None


def init_dependencies(
    cache: RedisCache,
    google_client: GoogleMapsClient,
    sensor_client: SensorServiceClient,
) -> None:
    """Initialize shared singletons during lifespan startup."""
    global _cache, _google_client, _sensor_client, _calibration_model
    _cache = cache
    _google_client = google_client
    _sensor_client = sensor_client
    _calibration_model = CalibrationModel()


def get_air_quality_service():
    """Provide an AirQualityApplicationService instance.

    The service is constructed from the shared singletons that were
    initialized at startup. This avoids creating new Redis/HTTP
    connections per request.
    """
    from ...application.services.air_quality_application_service import (
        AirQualityApplicationService,
    )

    return AirQualityApplicationService(
        aqi_calculator=AQICalculator(),
        prediction_service=PredictionService(),
        cache=_cache or RedisCache(),
        google_client=_google_client or GoogleMapsClient(),
        sensor_client=_sensor_client,
        calibration_model=_calibration_model or CalibrationModel(),
        cross_validator=CrossValidationService(),
    )
