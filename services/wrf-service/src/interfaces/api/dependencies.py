"""Dependency injection for WRF Service."""
import logging
from functools import lru_cache

from ...application.services.wrf_application_service import WRFApplicationService
from ...infrastructure.config import settings
from ...infrastructure.external.gfs_data_downloader import GFSDataDownloader
from ...infrastructure.wrf.wrf_model_runner import WRFModelRunner
from ...infrastructure.persistence.database import get_db_manager, get_session
from ...infrastructure.persistence.wrf_repository_impl import (
    SQLAlchemyWRFSimulationRepository,
)
from .wrf_controller import WRFController

logger = logging.getLogger(__name__)


@lru_cache
def get_gfs_downloader() -> GFSDataDownloader:
    """Get GFS data downloader instance."""
    return GFSDataDownloader()


@lru_cache
def get_wrf_runner() -> WRFModelRunner:
    """Get WRF model runner instance."""
    return WRFModelRunner()


async def get_repository():
    """Get WRF simulation repository."""
    db_mgr = get_db_manager(settings.from_env().DATABASE_URL if hasattr(settings, 'DATABASE_URL') else "mysql+aiomysql://root:Mysql_2026@mysql:3306/wrf_db?charset=utf8mb4")
    
    async for session in db_mgr.get_session():
        yield SQLAlchemyWRFSimulationRepository(session)


async def get_application_service() -> WRFApplicationService:
    """Get WRF application service."""
    db_mgr = get_db_manager("mysql+aiomysql://root:Mysql_2026@mysql:3306/wrf_db?charset=utf8mb4")
    
    async for session in db_mgr.get_session():
        repository = SQLAlchemyWRFSimulationRepository(session)
        gfs_downloader = get_gfs_downloader()
        wrf_runner = get_wrf_runner()

        yield WRFApplicationService(
            repository=repository,
            gfs_downloader=gfs_downloader,
            wrf_runner=wrf_runner,
        )


async def get_wrf_controller() -> WRFController:
    """Get WRF controller."""
    db_mgr = get_db_manager("mysql+aiomysql://root:Mysql_2026@mysql:3306/wrf_db?charset=utf8mb4")
    
    async for session in db_mgr.get_session():
        repository = SQLAlchemyWRFSimulationRepository(session)
        gfs_downloader = get_gfs_downloader()
        wrf_runner = get_wrf_runner()

        service = WRFApplicationService(
            repository=repository,
            gfs_downloader=gfs_downloader,
            wrf_runner=wrf_runner,
        )

        yield WRFController(service)
