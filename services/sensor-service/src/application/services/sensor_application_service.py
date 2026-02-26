"""Sensor application service."""


class SensorApplicationService:
    """Orchestrates sensor-related use cases."""

    def __init__(self, sensor_repository, reading_repository, event_publisher):
        self.sensor_repository = sensor_repository
        self.reading_repository = reading_repository
        self.event_publisher = event_publisher

    async def register_sensor(self, command):
        pass

    async def submit_reading(self, command):
        pass

    async def calibrate_sensor(self, command):
        pass

    async def get_sensor(self, sensor_id):
        pass

    async def get_readings(self, query):
        pass
