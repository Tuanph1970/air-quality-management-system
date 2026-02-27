"""Query to get AQI forecast."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID


@dataclass
class GetForecastQuery:
    """Query to get AQI forecast for a location.

    Attributes
    ----------
    latitude:
        Location latitude
    longitude:
        Location longitude
    hours:
        Number of hours to forecast (default 24)
    interval_hours:
        Interval between forecast points (default 1)
    """

    latitude: float
    longitude: float
    hours: int = 24
    interval_hours: int = 1


@dataclass
class ForecastDataPoint:
    """A single forecast data point.

    Attributes
    ----------
    timestamp:
        Forecast timestamp
    predicted_aqi:
        Predicted AQI value
    min_aqi:
        Minimum expected AQI (confidence lower bound)
    max_aqi:
        Maximum expected AQI (confidence upper bound)
    confidence:
        Confidence level (0.0 to 1.0)
    trend:
        Trend direction (IMPROVING, STABLE, WORSENING)
    level:
        AQI level category
    """

    timestamp: datetime
    predicted_aqi: int
    min_aqi: int
    max_aqi: int
    confidence: float
    trend: str
    level: str


@dataclass
class GetForecastResult:
    """Result of forecast query.

    Attributes
    ----------
    location_lat:
        Forecast location latitude
    location_lng:
        Forecast location longitude
    generated_at:
        When the forecast was generated
    forecast_hours:
        Total forecast duration in hours
    current_aqi:
        Current AQI at forecast time
    data_points:
        List of forecast data points
    average_aqi:
        Average predicted AQI
    max_aqi:
        Maximum predicted AQI
    overall_trend:
        Overall trend direction
    health_recommendation:
        General health recommendation
    """

    location_lat: float
    location_lng: float
    generated_at: datetime
    forecast_hours: int
    current_aqi: int = 0
    data_points: List[ForecastDataPoint] = field(default_factory=list)
    average_aqi: int = 0
    max_aqi: int = 0
    overall_trend: str = "STABLE"
    health_recommendation: str = ""

    @property
    def summary(self) -> Dict:
        """Get a summary of the forecast."""
        if not self.data_points:
            return {
                "status": "NO_DATA",
                "message": "Unable to generate forecast",
            }

        if self.max_aqi > 200:
            outlook = "POOR"
            recommendation = "Consider reducing outdoor activities during peak pollution hours."
        elif self.max_aqi > 100:
            outlook = "MODERATE"
            recommendation = "Sensitive groups should monitor air quality and limit prolonged outdoor exertion."
        else:
            outlook = "GOOD"
            recommendation = "Air quality is expected to be satisfactory."

        return {
            "status": "OK",
            "average_aqi": self.average_aqi,
            "max_aqi": self.max_aqi,
            "overall_trend": self.overall_trend,
            "outlook": outlook,
            "recommendation": recommendation,
        }
