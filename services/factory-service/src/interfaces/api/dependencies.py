"""FastAPI dependency injection wiring for the factory service.

Connects the interface layer to the application and infrastructure
layers.  Each dependency is an async generator or callable that FastAPI
resolves automatically via ``Depends()``.
"""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.factory_application_service import (
    FactoryApplicationService,
)
from ...infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher
from ...infrastructure.persistence.database import get_db
from ...infrastructure.persistence.factory_repository_impl import (
    SQLAlchemyFactoryRepository,
)


# ---------------------------------------------------------------------------
# Module-level singleton for the event publisher.
#
# Created once and shared across requests.  ``connect()`` / ``close()``
# are called from the FastAPI lifespan hook in ``routes.py``.
# ---------------------------------------------------------------------------
_event_publisher: RabbitMQEventPublisher | None = None


def init_event_publisher() -> RabbitMQEventPublisher:
    """Initialise the module-level event publisher singleton."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = RabbitMQEventPublisher()
    return _event_publisher


def get_event_publisher() -> RabbitMQEventPublisher:
    """Return the event publisher singleton.

    Raises ``RuntimeError`` if called before ``init_event_publisher()``.
    """
    if _event_publisher is None:
        raise RuntimeError(
            "Event publisher not initialised. "
            "Call init_event_publisher() during application startup."
        )
    return _event_publisher


# ---------------------------------------------------------------------------
# Application service — the primary dependency for controllers
# ---------------------------------------------------------------------------
async def get_factory_service(
    session: AsyncSession = Depends(get_db),
    publisher: RabbitMQEventPublisher = Depends(get_event_publisher),
) -> FactoryApplicationService:
    """Build a ``FactoryApplicationService`` with its two dependencies.

    A fresh ``SQLAlchemyFactoryRepository`` is created per request
    (bound to the request-scoped session), while the event publisher
    is a long-lived singleton.
    """
    repository = SQLAlchemyFactoryRepository(session)
    return FactoryApplicationService(
        factory_repository=repository,
        event_publisher=publisher,
    )
