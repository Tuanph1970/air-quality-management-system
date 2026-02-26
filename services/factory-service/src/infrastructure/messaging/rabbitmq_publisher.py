"""RabbitMQ event publisher adapter for the factory service.

Wraps the shared ``RabbitMQPublisher`` and satisfies the application
layer's ``EventPublisher`` protocol by always routing events to the
``FACTORY_EXCHANGE``.
"""
from __future__ import annotations

import logging
from typing import Optional

from shared.events.base_event import DomainEvent
from shared.messaging.config import FACTORY_EXCHANGE
from shared.messaging.publisher import RabbitMQPublisher

logger = logging.getLogger(__name__)


class RabbitMQEventPublisher:
    """Adapter that fulfils the ``EventPublisher`` protocol.

    The application service calls ``publish(event)`` with a single
    argument.  This adapter delegates to the shared
    ``RabbitMQPublisher.publish(event, exchange)`` adding the factory
    exchange automatically.

    Parameters
    ----------
    url:
        AMQP connection string.  When ``None`` the shared library's
        default (from ``RABBITMQ_URL`` env var) is used.
    """

    def __init__(self, url: Optional[str] = None) -> None:
        kwargs = {"url": url} if url else {}
        self._publisher = RabbitMQPublisher(**kwargs)

    # ------------------------------------------------------------------
    # Lifecycle — called by the FastAPI lifespan hook
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Open the RabbitMQ connection and declare exchanges."""
        await self._publisher.connect()
        logger.info("Factory event publisher connected")

    async def close(self) -> None:
        """Gracefully close the RabbitMQ connection."""
        await self._publisher.close()
        logger.info("Factory event publisher closed")

    # ------------------------------------------------------------------
    # EventPublisher protocol
    # ------------------------------------------------------------------
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to the factory exchange.

        The event's ``event_type`` is used as the routing key.
        """
        await self._publisher.publish(
            event=event,
            exchange=FACTORY_EXCHANGE,
        )

    # ------------------------------------------------------------------
    # Async context-manager support
    # ------------------------------------------------------------------
    async def __aenter__(self) -> RabbitMQEventPublisher:
        await self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
