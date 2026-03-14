"""Database connection and session management."""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session_factory = None

    def create_engine(self) -> None:
        """Create the database engine."""
        logger.info(f"Creating database engine for {self.database_url}")

        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )

        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Database engine created successfully")

    async def close(self) -> None:
        """Close the database engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self.async_session_factory:
            self.create_engine()

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """Create all tables in the database with retry for slow hardware."""
        if not self.engine:
            self.create_engine()

        from .models import Base
        from shared.utils.startup import init_db_with_retry

        await init_db_with_retry(self.engine, Base.metadata)
        logger.info("Database tables created successfully")


# Global database manager instance
db_manager: DatabaseManager | None = None


def get_db_manager(database_url: str | None = None) -> DatabaseManager:
    """Get or create the database manager."""
    global db_manager

    if db_manager is None:
        if not database_url:
            raise ValueError("Database URL required")
        db_manager = DatabaseManager(database_url)
        db_manager.create_engine()

    return db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    db_mgr = get_db_manager()
    async for session in db_mgr.get_session():
        yield session
