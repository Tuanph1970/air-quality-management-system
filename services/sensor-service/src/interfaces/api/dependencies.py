"""FastAPI dependency injection wiring for the sensor service.

Connects the interface layer to the application and infrastructure
layers.  Each dependency is an async generator or callable that FastAPI
resolves automatically via ``Depends()``.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.services.sensor_application_service import (
    SensorApplicationService,
)
from ...infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher
from ...infrastructure.persistence.reading_repository_impl import (
    SQLAlchemyReadingRepository,
)
from ...infrastructure.persistence.sensor_repository_impl import (
    SQLAlchemySensorRepository,
)
from ...infrastructure.persistence.timescale_database import get_db


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
async def get_sensor_service(
    session: AsyncSession = Depends(get_db),
    publisher: RabbitMQEventPublisher = Depends(get_event_publisher),
) -> SensorApplicationService:
    """Build a ``SensorApplicationService`` with its three dependencies.

    Fresh repositories are created per request (bound to the
    request-scoped session), while the event publisher is a long-lived
    singleton.
    """
    sensor_repository = SQLAlchemySensorRepository(session)
    reading_repository = SQLAlchemyReadingRepository(session)
    return SensorApplicationService(
        sensor_repository=sensor_repository,
        reading_repository=reading_repository,
        event_publisher=publisher,
    )
