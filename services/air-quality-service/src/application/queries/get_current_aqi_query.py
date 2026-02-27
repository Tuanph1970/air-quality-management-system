"""Query to get current AQI for a location."""
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID


@dataclass
class GetCurrentAQIQuery:
    """Query to get current AQI for a specific location.

    Attributes
    ----------
    latitude:
        Location latitude
    longitude:
        Location longitude
    radius_km:
        Search radius in kilometers (default 10km)
    include_pollutants:
        Whether to include individual pollutant AQIs
    """

    latitude: float
    longitude: float
    radius_km: float = 10.0
    include_pollutants: bool = True


@dataclass
class GetCurrentAQIResult:
    """Result of current AQI query.

    Attributes
    ----------
    location_lat:
        Location latitude
    location_lng:
        Location longitude
    aqi_value:
        Overall AQI value (0-500)
    level:
        AQI level (GOOD, MODERATE, etc.)
    category:
        Human-readable category name
    color:
        Hex color code for display
    dominant_pollutant:
        Pollutant causing the highest AQI
    pollutants:
        Individual pollutant concentrations and AQIs
    health_message:
        Health impact description
    caution_message:
        Caution statement
    timestamp:
        When the reading was taken
    data_source:
        Source of the data (sensor, model, etc.)
    """

    location_lat: float
    location_lng: float
    aqi_value: int
    level: str
    category: str
    color: str
    dominant_pollutant: str
    pollutants: Dict = field(default_factory=dict)
    health_message: str = ""
    caution_message: str = ""
    timestamp: str = ""
    data_source: str = "sensor"
