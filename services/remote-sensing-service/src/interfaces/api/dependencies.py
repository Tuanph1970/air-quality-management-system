"""FastAPI dependency injection wiring for the remote-sensing service.

Connects the interface layer to the application and infrastructure
layers.  Each dependency is an async generator or callable that FastAPI
resolves automatically via ``Depends()``.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.data_fusion_application_service import (
    DataFusionApplicationService,
)
from ...application.services.excel_import_service import ExcelImportService
from ...application.services.satellite_data_service import SatelliteDataService
from ...domain.services.calibration_service import CalibrationService
from ...domain.services.cross_validation_service import CrossValidationService
from ...domain.services.data_fusion_service import DataFusionService
from ...infrastructure.external.copernicus_cams_client import CopernicusCAMSClient
from ...infrastructure.external.nasa_earthdata_client import NASAEarthdataClient
from ...infrastructure.external.sensor_service_client import SensorServiceClient
from ...infrastructure.external.sentinel_hub_client import SentinelHubClient
from ...infrastructure.messaging.rabbitmq_publisher import RemoteSensingEventPublisher
from ...infrastructure.parsers.excel_parser import ExcelParser
from ...infrastructure.persistence.database import get_db
from ...infrastructure.persistence.excel_import_repository_impl import (
    SQLAlchemyExcelImportRepository,
)
from ...infrastructure.persistence.fused_data_repository_impl import (
    SQLAlchemyFusedDataRepository,
)
from ...infrastructure.persistence.satellite_data_repository_impl import (
    SQLAlchemySatelliteDataRepository,
)


# ---------------------------------------------------------------------------
# Module-level singletons (initialised from lifespan hook in routes.py)
# ---------------------------------------------------------------------------
_event_publisher: RemoteSensingEventPublisher | None = None
_scheduler = None  # SatelliteScheduler — set by routes.py lifespan


def init_event_publisher() -> RemoteSensingEventPublisher:
    """Initialise the module-level event publisher singleton."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = RemoteSensingEventPublisher()
    return _event_publisher


def get_event_publisher() -> RemoteSensingEventPublisher:
    """Return the event publisher singleton."""
    if _event_publisher is None:
        raise RuntimeError(
            "Event publisher not initialised. "
            "Call init_event_publisher() during application startup."
        )
    return _event_publisher


def set_scheduler(scheduler) -> None:
    """Store the scheduler singleton for dependency access."""
    global _scheduler
    _scheduler = scheduler


def get_scheduler():
    """Return the scheduler singleton."""
    return _scheduler


# ---------------------------------------------------------------------------
# Infrastructure clients — created per-request with config values
# ---------------------------------------------------------------------------
def _get_cams_client() -> CopernicusCAMSClient:
    from ...config import settings
    return CopernicusCAMSClient(api_key=settings.COPERNICUS_API_KEY)


def _get_nasa_client() -> NASAEarthdataClient:
    from ...config import settings
    return NASAEarthdataClient(token=settings.NASA_EARTHDATA_TOKEN)


def _get_sentinel_client() -> SentinelHubClient:
    from ...config import settings
    return SentinelHubClient(
        client_id=settings.SENTINEL_HUB_CLIENT_ID,
        client_secret=settings.SENTINEL_HUB_CLIENT_SECRET,
    )


def _get_sensor_client() -> SensorServiceClient:
    from ...config import settings
    return SensorServiceClient(base_url=settings.SENSOR_SERVICE_URL)


# ---------------------------------------------------------------------------
# Application services — the primary dependencies for controllers
# ---------------------------------------------------------------------------
async def get_satellite_service(
    session: AsyncSession = Depends(get_db),
) -> SatelliteDataService:
    """Build a ``SatelliteDataService`` wired with all infrastructure deps."""
    repository = SQLAlchemySatelliteDataRepository(session)
    return SatelliteDataService(
        repository=repository,
        cams_client=_get_cams_client(),
        nasa_client=_get_nasa_client(),
        sentinel_client=_get_sentinel_client(),
        event_publisher=get_event_publisher(),
    )


async def get_excel_import_service(
    session: AsyncSession = Depends(get_db),
) -> ExcelImportService:
    """Build an ``ExcelImportService`` wired with repository and parser."""
    repository = SQLAlchemyExcelImportRepository(session)
    return ExcelImportService(
        repository=repository,
        parser=ExcelParser(),
        event_publisher=get_event_publisher(),
    )


async def get_fusion_service(
    session: AsyncSession = Depends(get_db),
) -> DataFusionApplicationService:
    """Build a ``DataFusionApplicationService`` wired with all deps."""
    satellite_repo = SQLAlchemySatelliteDataRepository(session)
    fused_repo = SQLAlchemyFusedDataRepository(session)

    return DataFusionApplicationService(
        satellite_repo=satellite_repo,
        fused_repo=fused_repo,
        fusion_service=DataFusionService(),
        calibration_service=CalibrationService(),
        cross_validation_service=CrossValidationService(),
        sensor_client=_get_sensor_client(),
        event_publisher=get_event_publisher(),
    )
