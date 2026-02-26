"""Event consumer endpoints for alert service."""


class EventConsumerEndpoints:
    """Handles incoming domain events from message broker."""

    async def on_sensor_reading_created(self, event):
        pass

    async def on_factory_suspended(self, event):
        pass
