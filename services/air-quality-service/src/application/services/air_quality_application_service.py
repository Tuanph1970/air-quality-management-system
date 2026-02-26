"""Air quality application service."""


class AirQualityApplicationService:
    """Orchestrates air quality use cases."""

    def __init__(self, aqi_calculator, prediction_service, cache, maps_client=None):
        self.aqi_calculator = aqi_calculator
        self.prediction_service = prediction_service
        self.cache = cache
        self.maps_client = maps_client

    async def get_current_aqi(self, query):
        pass

    async def get_forecast(self, query):
        pass

    async def get_map_data(self, query):
        pass
