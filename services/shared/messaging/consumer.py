"""RabbitMQ event consumer with automatic reconnection.

Usage::

    consumer = RabbitMQConsumer(rabbitmq_url)
    await consumer.connect()

    async def on_reading(event_data: dict, message: IncomingMessage) -> None:
        reading = SensorReadingCreated.from_dict(event_data)
        ...  # process

    await consumer.subscribe(
        queue=ALERT_SENSOR_READINGS_QUEUE,
        exchange=SENSOR_EXCHANGE,
        routing_keys=["sensor.reading.created"],
        handler=on_reading,
    )

    await consumer.start_consuming()   # blocks until cancelled / closed
    await consumer.close()

The consumer uses ``aio_pika.connect_robust`` for transparent
reconnection.  Queues are declared as *durable* so messages are not
lost across broker restarts.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)

from .config import (
    ALERT_EXCHANGE,
    FACTORY_EXCHANGE,
    FUSION_EXCHANGE,
    MAX_RECONNECT_ATTEMPTS,
    PREFETCH_COUNT,
    RABBITMQ_URL,
    RECONNECT_INTERVAL,
    SATELLITE_EXCHANGE,
    SENSOR_EXCHANGE,
    QueueBinding,
)

logger = logging.getLogger(__name__)

# Type alias for the handler signature each subscriber must implement.
#   async def handler(event_data: dict, message: AbstractIncomingMessage) -> None
EventHandler = Callable[
    [Dict[str, Any], AbstractIncomingMessage],
    Coroutine[Any, Any, None],
]

_ALL_EXCHANGES = [FACTORY_EXCHANGE, SENSOR_EXCHANGE, ALERT_EXCHANGE, SATELLITE_EXCHANGE, FUSION_EXCHANGE]


class RabbitMQConsumer:
    """Subscribes to RabbitMQ queues and dispatches events to handlers.

    Parameters
    ----------
    url:
        AMQP connection string.
    prefetch_count:
        Per-channel QoS prefetch limit.  Controls how many un-acked
        messages the broker will push to this consumer at once.
    """

    def __init__(
        self,
        url: str = RABBITMQ_URL,
        prefetch_count: int = PREFETCH_COUNT,
    ) -> None:
        self._url = url
        self._prefetch_count = prefetch_count

        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._exchanges: Dict[str, AbstractExchange] = {}
        self._queues: Dict[str, AbstractQueue] = {}
        self._consuming = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Open a robust connection, channel, and declare exchanges."""
        if self._connection and not self._connection.is_closed:
            return

        logger.info("Connecting consumer to RabbitMQ at %s", self._url)

        reconnect_kw = {}
        if MAX_RECONNECT_ATTEMPTS > 0:
            reconnect_kw["reconnect_interval"] = RECONNECT_INTERVAL

        self._connection = await aio_pika.connect_robust(
            self._url,
            **reconnect_kw,
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=self._prefetch_count)

        for name in _ALL_EXCHANGES:
            exchange = await self._channel.declare_exchange(
                name,
                type=ExchangeType.TOPIC,
                durable=True,
            )
            self._exchanges[name] = exchange
            logger.debug("Declared exchange %s", name)

        logger.info("Consumer connected (prefetch=%d)", self._prefetch_count)

    async def close(self) -> None:
        """Cancel all consumers and close the connection."""
        self._consuming = False

        for queue in self._queues.values():
            try:
                await queue.cancel(queue.name)
            except Exception:  # noqa: BLE001
                pass  # best-effort during shutdown

        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

        self._channel = None
        self._connection = None
        self._exchanges.clear()
        self._queues.clear()
        logger.info("Consumer connection closed")

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------
    async def subscribe(
        self,
        queue: str,
        exchange: str,
        routing_keys: List[str],
        handler: EventHandler,
    ) -> None:
        """Declare a durable queue, bind it, and start consuming.

        Parameters
        ----------
        queue:
            Queue name (from ``config.py`` constants).
        exchange:
            Exchange to bind to.
        routing_keys:
            One or more topic-style routing-key patterns.
        handler:
            Async callable ``(event_data, message) -> None``.
            The handler **must** ack or nack the message.  If the
            handler raises, the message is automatically nacked and
            requeued.
        """
        if not self._channel or self._channel.is_closed:
            await self.connect()

        target_exchange = self._exchanges.get(exchange)
        if target_exchange is None:
            raise ValueError(f"Unknown exchange '{exchange}'")

        declared_queue = await self._channel.declare_queue(
            queue,
            durable=True,
        )

        for key in routing_keys:
            await declared_queue.bind(target_exchange, routing_key=key)
            logger.debug("Bound %s -> %s [%s]", queue, exchange, key)

        # Wrap the user handler so we deserialize JSON and handle errors.
        async def _on_message(message: AbstractIncomingMessage) -> None:
            await self._dispatch(message, handler)

        await declared_queue.consume(_on_message, consumer_tag=queue)
        self._queues[queue] = declared_queue
        logger.info(
            "Subscribed queue=%s exchange=%s keys=%s",
            queue,
            exchange,
            routing_keys,
        )

    async def subscribe_bindings(
        self,
        bindings: List[QueueBinding],
        handlers: Dict[str, EventHandler],
    ) -> None:
        """Convenience: subscribe to a list of ``QueueBinding`` at once.

        Parameters
        ----------
        bindings:
            Typically one of the ``*_SERVICE_BINDINGS`` lists from
            ``config.py``.
        handlers:
            Mapping of ``queue_name -> handler``.  If a binding's queue
            is not present in this dict it is silently skipped (allows
            incremental handler implementation).
        """
        for binding in bindings:
            handler = handlers.get(binding.queue)
            if handler is None:
                logger.warning(
                    "No handler registered for queue %s – skipping",
                    binding.queue,
                )
                continue
            await self.subscribe(
                queue=binding.queue,
                exchange=binding.exchange,
                routing_keys=binding.routing_keys,
                handler=handler,
            )

    # ------------------------------------------------------------------
    # Blocking consume loop
    # ------------------------------------------------------------------
    async def start_consuming(self) -> None:
        """Block until ``close()`` is called or the connection drops.

        In practice each service calls this in an ``asyncio.Task`` so
        the FastAPI event loop keeps running alongside consumption.
        """
        if not self._connection:
            raise RuntimeError("Call connect() before start_consuming()")

        self._consuming = True
        logger.info("Consumer is now listening on %d queue(s)", len(self._queues))

        try:
            # aio_pika robust connections stay alive and auto-reconnect.
            # We simply await the close future which only resolves when
            # *we* call close() or the connection is irrecoverably lost.
            await self._connection.close_callbacks.wait()
        except Exception:  # noqa: BLE001
            if self._consuming:
                logger.exception("Consumer loop terminated unexpectedly")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    @staticmethod
    async def _dispatch(
        message: AbstractIncomingMessage,
        handler: EventHandler,
    ) -> None:
        """Deserialize JSON body and forward to the handler."""
        try:
            body = json.loads(message.body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.error(
                "Failed to decode message body (id=%s) – rejecting",
                message.message_id,
            )
            await message.reject(requeue=False)
            return

        try:
            await handler(body, message)
        except Exception:
            logger.exception(
                "Handler raised for message %s – nacking with requeue",
                message.message_id,
            )
            await message.nack(requeue=True)

    # ------------------------------------------------------------------
    # Async context-manager support
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "RabbitMQConsumer":
        await self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()
