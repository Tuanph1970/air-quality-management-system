"""Shared RabbitMQ messaging library for inter-service communication."""

from .config import (
    RABBITMQ_URL,
    FACTORY_EXCHANGE,
    SENSOR_EXCHANGE,
    ALERT_EXCHANGE,
    PREFETCH_COUNT,
    QueueBinding,
    SERVICE_BINDINGS,
)
from .publisher import RabbitMQPublisher
from .consumer import RabbitMQConsumer

__all__ = [
    # Connection
    "RABBITMQ_URL",
    # Exchanges
    "FACTORY_EXCHANGE",
    "SENSOR_EXCHANGE",
    "ALERT_EXCHANGE",
    # Config
    "PREFETCH_COUNT",
    "QueueBinding",
    "SERVICE_BINDINGS",
    # Classes
    "RabbitMQPublisher",
    "RabbitMQConsumer",
]
