"""RabbitMQ event publisher with automatic reconnection.

Usage::

    publisher = RabbitMQPublisher(rabbitmq_url)
    await publisher.connect()

    event = FactoryCreated(factory_id=uuid4(), name="Acme")
    await publisher.publish(event, exchange=FACTORY_EXCHANGE)

    await publisher.close()

The publisher uses ``aio_pika.connect_robust`` which transparently
reconnects on broker restarts or transient network failures.  Messages
are persisted (``delivery_mode=PERSISTENT``) so they survive broker
restarts when the target queue is durable.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, Optional

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractRobustConnection

from ..events.base_event import DomainEvent
from .config import (
    ALERT_EXCHANGE,
    FACTORY_EXCHANGE,
    MAX_RECONNECT_ATTEMPTS,
    RABBITMQ_URL,
    RECONNECT_INTERVAL,
    SENSOR_EXCHANGE,
)

logger = logging.getLogger(__name__)

# All known exchanges – declared once on first use.
_ALL_EXCHANGES = [FACTORY_EXCHANGE, SENSOR_EXCHANGE, ALERT_EXCHANGE]


class RabbitMQPublisher:
    """Publishes ``DomainEvent`` instances to RabbitMQ topic exchanges.

    Parameters
    ----------
    url:
        AMQP connection string.  Falls back to the ``RABBITMQ_URL``
        environment variable / default from ``config.py``.
    """

    def __init__(self, url: str = RABBITMQ_URL) -> None:
        self._url = url
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._exchanges: Dict[str, AbstractExchange] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Open a robust connection and declare all topic exchanges."""
        if self._connection and not self._connection.is_closed:
            return

        logger.info("Connecting publisher to RabbitMQ at %s", self._url)

        reconnect_kw = {}
        if MAX_RECONNECT_ATTEMPTS > 0:
            reconnect_kw["reconnect_interval"] = RECONNECT_INTERVAL
            # aio_pika 9.x: fail_fast is not a kwarg; robust connection
            # retries indefinitely by default which is the safest mode.

        self._connection = await aio_pika.connect_robust(
            self._url,
            **reconnect_kw,
        )
        self._channel = await self._connection.channel()

        # Declare every exchange idempotently so publishers don't need
        # to worry about ordering.
        for name in _ALL_EXCHANGES:
            exchange = await self._channel.declare_exchange(
                name,
                type=ExchangeType.TOPIC,
                durable=True,
            )
            self._exchanges[name] = exchange
            logger.debug("Declared exchange %s", name)

        logger.info("Publisher connected and exchanges declared")

    async def close(self) -> None:
        """Gracefully shut down channel and connection."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

        self._channel = None
        self._connection = None
        self._exchanges.clear()
        logger.info("Publisher connection closed")

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------
    async def publish(
        self,
        event: DomainEvent,
        exchange: str,
        routing_key: Optional[str] = None,
    ) -> None:
        """Serialize and publish a domain event.

        Parameters
        ----------
        event:
            Any ``DomainEvent`` subclass.  Serialized via ``to_dict()``.
        exchange:
            Target exchange name (e.g. ``FACTORY_EXCHANGE``).
        routing_key:
            Explicit routing key.  When ``None`` the event's
            ``event_type`` attribute is used (e.g. ``"factory.created"``),
            which naturally matches topic-exchange binding patterns.
        """
        if not self._channel or self._channel.is_closed:
            await self.connect()

        target = self._exchanges.get(exchange)
        if target is None:
            raise ValueError(
                f"Unknown exchange '{exchange}'. "
                f"Known exchanges: {list(self._exchanges)}"
            )

        key = routing_key or event.event_type
        body = json.dumps(event.to_dict()).encode()

        message = Message(
            body=body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=str(event.event_id),
            timestamp=event.occurred_at,
            type=event.event_type,
        )

        await target.publish(message, routing_key=key)
        logger.info(
            "Published %s to %s [routing_key=%s, id=%s]",
            event.event_type,
            exchange,
            key,
            event.event_id,
        )

    # ------------------------------------------------------------------
    # Async context-manager support
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "RabbitMQPublisher":
        await self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
