"""RabbitMQ event publisher."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional

import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType

logger = logging.getLogger(__name__)


# Global publisher instance
_publisher: Optional["RabbitMQPublisher"] = None


class RabbitMQPublisher:
    """RabbitMQ publisher for domain events.
    
    Publishes events to a fanout exchange for broadcast to all
    interested services.
    
    Example:
        publisher = RabbitMQPublisher(rabbitmq_url)
        await publisher.connect()
        await publisher.publish(event)
    """
    
    def __init__(self, rabbitmq_url: str):
        """Initialize publisher.
        
        Args:
            rabbitmq_url: RabbitMQ connection URL (amqp://...)
        """
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to RabbitMQ and set up exchange."""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Set up fanout exchange for broadcast
            self.exchange = await self.channel.declare_exchange(
                "aqms.events",
                ExchangeType.FANOUT,
                durable=True,
            )
            
            self._connected = True
            logger.info("RabbitMQ publisher connected")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def publish(self, event: Any) -> None:
        """Publish a domain event.
        
        Args:
            event: Domain event to publish
        """
        if not self._connected:
            logger.warning("RabbitMQ not connected, skipping event publish")
            return
        
        try:
            # Convert event to dict
            if hasattr(event, "__dataclass_fields__"):
                event_dict = asdict(event)
            elif hasattr(event, "dict"):
                event_dict = event.dict()
            else:
                event_dict = vars(event)
            
            # Add metadata
            event_dict["_published_at"] = datetime.utcnow().isoformat()
            event_dict["_event_type"] = getattr(event, "event_type", "unknown")
            
            # Create message
            message = Message(
                body=json.dumps(event_dict).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                message_id=getattr(event, "event_id", None),
                timestamp=datetime.utcnow(),
            )
            
            # Publish to exchange
            await self.channel.default_exchange.publish(
                message,
                routing_key="aqms.events",
            )
            
            logger.debug(f"Published event: {event_dict.get('_event_type')}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}", exc_info=True)
    
    async def close(self) -> None:
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            self._connected = False
            logger.info("RabbitMQ publisher closed")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to RabbitMQ."""
        return self._connected and self.connection is not None


def init_event_publisher(rabbitmq_url: Optional[str] = None) -> RabbitMQPublisher:
    """Initialize the global event publisher.
    
    Args:
        rabbitmq_url: Optional RabbitMQ URL (uses env var if not provided)
        
    Returns:
        RabbitMQPublisher instance
    """
    global _publisher
    
    if _publisher is None:
        from ...config import settings
        
        url = rabbitmq_url or settings.RABBITMQ_URL
        _publisher = RabbitMQPublisher(url)
    
    return _publisher


def get_event_publisher() -> RabbitMQPublisher:
    """Get the global event publisher instance.
    
    Returns:
        RabbitMQPublisher instance
        
    Raises:
        RuntimeError: If publisher not initialized
    """
    if _publisher is None:
        raise RuntimeError(
            "Event publisher not initialized. Call init_event_publisher() first."
        )
    return _publisher
