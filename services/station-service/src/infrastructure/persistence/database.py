"""Database configuration and session management."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Global engine and session factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Get or create the database engine.
    
    Args:
        database_url: Optional database URL (uses env var if not provided)
        
    Returns:
        AsyncEngine instance
    """
    global _engine
    
    if _engine is None:
        from ...config import settings
        
        db_url = database_url or settings.DATABASE_URL
        
        _engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        logger.info("Database engine created")
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory.
    
    Returns:
        AsyncSession factory
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("Session factory created")
    
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session context manager.
    
    Yields:
        AsyncSession instance
        
    Example:
        async with get_db_session() as session:
            # use session
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_database() -> None:
    """Initialize database tables with retry for slow hardware."""
    from shared.utils.startup import init_db_with_retry

    engine = get_engine()
    await init_db_with_retry(engine, Base.metadata)
    logger.info("Database tables created")


async def dispose_database() -> None:
    """Dispose of the database engine."""
    global _engine, _session_factory
    
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database engine disposed")
        _engine = None
        _session_factory = None
