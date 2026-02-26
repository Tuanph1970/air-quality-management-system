"""Event consumers for air quality service."""


class AirQualityEventConsumer:
    """Consumes sensor reading events to update AQI."""

    async def handle_sensor_reading(self, message):
        pass
