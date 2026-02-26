"""AQI calculator domain service."""


class AQICalculator:
    """Calculates Air Quality Index from pollutant readings."""

    def calculate_aqi(self, pm25: float = 0, pm10: float = 0, co: float = 0,
                      no2: float = 0, so2: float = 0, o3: float = 0) -> int:
        pass

    def get_aqi_level(self, aqi: int) -> str:
        pass
