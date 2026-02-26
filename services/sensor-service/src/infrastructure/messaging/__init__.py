"""Sensor service messaging infrastructure."""
from .rabbitmq_publisher import RabbitMQEventPublisher

__all__ = ["RabbitMQEventPublisher"]
