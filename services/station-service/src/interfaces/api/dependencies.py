"""Dependencies for dependency injection."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import AsyncGenerator

from ...application.services import StationApplicationService
from ...infrastructure.persistence import (
    get_db_session,
    SQLAlchemyStationRepository,
    SQLAlchemyReadingRepository,
)
from ...infrastructure.messaging import get_event_publisher

logger = logging.getLogger(__name__)


# Cache for application service instance
_app_service: StationApplicationService | None = None


async def get_db_session_context() -> AsyncGenerator:
    """Get database session context."""
    async with get_db_session() as session:
        yield session


def get_station_app_service() -> StationApplicationService:
    """Get or create the station application service.
    
    This is a synchronous getter for use in FastAPI dependencies.
    For async initialization, use init_application_service().
    
    Returns:
        StationApplicationService instance
    """
    global _app_service
    
    if _app_service is None:
        # Create repositories with a new session
        # Note: In production, manage session lifecycle per request
        from ...infrastructure.persistence.database import get_session_factory
        from sqlalchemy.ext.asyncio import AsyncSession
        
        session_factory = get_session_factory()
        session = session_factory()
        
        station_repo = SQLAlchemyStationRepository(session)
        reading_repo = SQLAlchemyReadingRepository(session)
        
        # Try to get event publisher (may not be connected)
        try:
            event_publisher = get_event_publisher()
        except RuntimeError:
            event_publisher = None
        
        _app_service = StationApplicationService(
            station_repository=station_repo,
            reading_repository=reading_repo,
            event_publisher=event_publisher,
        )
        
        logger.info("Created station application service")
    
    return _app_service


async def init_application_service() -> StationApplicationService:
    """Initialize application service with proper async setup.
    
    Returns:
        StationApplicationService instance
    """
    async with get_db_session() as session:
        station_repo = SQLAlchemyStationRepository(session)
        reading_repo = SQLAlchemyReadingRepository(session)
        
        try:
            event_publisher = get_event_publisher()
        except RuntimeError:
            event_publisher = None
        
        return StationApplicationService(
            station_repository=station_repo,
            reading_repository=reading_repo,
            event_publisher=event_publisher,
        )
