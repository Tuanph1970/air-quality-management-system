"""RabbitMQ event publisher implementation."""


class RabbitMQPublisher:
    """Publishes domain events to RabbitMQ."""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url

    async def connect(self):
        pass

    async def publish(self, event) -> None:
        pass

    async def close(self):
        pass
