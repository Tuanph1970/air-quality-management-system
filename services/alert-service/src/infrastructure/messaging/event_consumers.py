"""Event consumers for alert service."""


class AlertEventConsumer:
    """Consumes events from other services (e.g., SensorReadingCreated)."""

    async def handle_sensor_reading(self, message):
        """Process incoming sensor readings and check thresholds."""
        pass
