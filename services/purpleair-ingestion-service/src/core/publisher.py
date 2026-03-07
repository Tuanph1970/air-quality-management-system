"""RabbitMQ event publisher."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import aio_pika
from aio_pika import Message, DeliveryMode

from .config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publish events to RabbitMQ."""
    
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            self._connected = True
            logger.info("RabbitMQ publisher connected")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def publish(self, event: Any) -> None:
        """Publish an event."""
        if not self._connected:
            logger.warning("RabbitMQ not connected, skipping event")
            return
        
        try:
            # Convert event to dict
            if hasattr(event, "to_dict"):
                event_dict = event.to_dict()
            elif hasattr(event, "__dataclass_fields__"):
                from dataclasses import asdict
                event_dict = asdict(event)
            else:
                event_dict = vars(event)
            
            message = Message(
                body=json.dumps(event_dict).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                timestamp=datetime.utcnow(),
            )
            
            await self.channel.default_exchange.publish(
                message,
                routing_key="aqms.events",
            )
            
            logger.debug(f"Published event: {event_dict.get('event_type')}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}", exc_info=True)
    
    async def close(self) -> None:
        """Close connection."""
        if self.connection:
            await self.connection.close()
            self._connected = False
            logger.info("RabbitMQ publisher closed")


# Global instance
_publisher: EventPublisher | None = None


def get_publisher() -> EventPublisher:
    """Get event publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher(settings.RABBITMQ_URL)
    return _publisher
