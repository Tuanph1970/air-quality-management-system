"""Weather variable types for WRF simulation."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class WeatherVariable(Enum):
    """Enum of weather variables that WRF can forecast."""

    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    WIND_SPEED = "wind_speed"
    WIND_DIRECTION = "wind_direction"
    PRESSURE = "pressure"
    PRECIPITATION = "precipitation"
    CLOUD_FRACTION = "cloud_fraction"
    RADIATION = "radiation"
    VERTICAL_VELOCITY = "vertical_velocity"


class AtmosphericLevel(Enum):
    """Atmospheric pressure levels for vertical data."""

    SURFACE = "surface"
    LEVEL_10M = "10m"
    LEVEL_2M = "2m"
    LEVEL_500MB = "500mb"
    LEVEL_700MB = "700mb"
    LEVEL_850MB = "850mb"
    LEVEL_1000MB = "1000mb"


@dataclass(frozen=True)
class WeatherDataPoint:
    """Value Object - Single weather data point at a specific location and time."""

    latitude: float
    longitude: float
    variable: WeatherVariable
    value: float
    unit: str
    level: AtmosphericLevel = AtmosphericLevel.SURFACE
    timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "variable": self.variable.value,
            "value": self.value,
            "unit": self.unit,
            "level": self.level.value,
            "timestamp": self.timestamp,
        }
