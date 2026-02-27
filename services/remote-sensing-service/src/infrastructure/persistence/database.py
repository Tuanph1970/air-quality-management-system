"""Async SQLAlchemy engine and session configuration.

Provides the ``AsyncEngine``, ``async_session_maker``, and a FastAPI-
compatible ``get_db()`` dependency that yields a scoped ``AsyncSession``.

Engine and session factory are created lazily to avoid import-time side
effects (e.g. requiring ``asyncpg`` when running tests without a database).
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


# ---------------------------------------------------------------------------
# Declarative base for all models in this service
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """SQLAlchemy declarative base for remote-sensing-service models."""


# ---------------------------------------------------------------------------
# Lazy engine & session factory
# ---------------------------------------------------------------------------
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the shared ``AsyncEngine``, creating it on first call."""
    global _engine
    if _engine is None:
        from ...config import settings

        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Return the shared session factory, creating it on first call."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` that is automatically closed on exit."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
