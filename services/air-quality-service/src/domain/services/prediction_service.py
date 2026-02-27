"""AQI Prediction domain service.

Provides simple AQI forecasting based on historical sensor data.
Uses a weighted moving average approach with trend analysis.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from statistics import mean, stdev


@dataclass
class SensorDataPoint:
    """A single sensor reading with timestamp."""

    timestamp: datetime
    pollutants: Dict[str, float]
    aqi: int


@dataclass
class ForecastDataPoint:
    """A forecasted AQI data point."""

    timestamp: datetime
    predicted_aqi: int
    confidence: float  # 0.0 to 1.0
    min_aqi: int
    max_aqi: int
    trend: str  # "IMPROVING", "STABLE", "WORSENING"


@dataclass
class AQIForecast:
    """Complete AQI forecast result."""

    location_lat: float
    location_lng: float
    generated_at: datetime
    forecast_hours: int
    data_points: List[ForecastDataPoint] = field(default_factory=list)

    @property
    def average_aqi(self) -> int:
        """Calculate average predicted AQI."""
        if not self.data_points:
            return 0
        return round(mean([dp.predicted_aqi for dp in self.data_points]))

    @property
    def max_aqi(self) -> int:
        """Get maximum predicted AQI."""
        if not self.data_points:
            return 0
        return max(dp.predicted_aqi for dp in self.data_points)

    @property
    def overall_trend(self) -> str:
        """Determine overall trend from forecast."""
        if len(self.data_points) < 2:
            return "STABLE"

        first_half = mean([dp.predicted_aqi for dp in self.data_points[:len(self.data_points)//2]])
        second_half = mean([dp.predicted_aqi for dp in self.data_points[len(self.data_points)//2:]])

        diff = second_half - first_half
        if diff > 10:
            return "WORSENING"
        elif diff < -10:
            return "IMPROVING"
        return "STABLE"


class PredictionService:
    """AQI Prediction domain service.

    Provides short-term AQI forecasting using historical data analysis.
    Uses weighted moving average with trend extrapolation.
    """

    def __init__(self):
        # Weights for recent vs older data (more recent = higher weight)
        self.recent_weight = 0.6
        self.older_weight = 0.4

    def predict_next_hours(
        self,
        sensor_data: List[SensorDataPoint],
        hours: int = 24,
        interval_hours: int = 1,
    ) -> AQIForecast:
        """Predict AQI for the next N hours.

        Uses weighted moving average and trend analysis to forecast
        future AQI values based on historical sensor data.

        Parameters
        ----------
        sensor_data:
            List of historical sensor data points (most recent last)
        hours:
            Number of hours to forecast
        interval_hours:
            Interval between forecast points

        Returns
        -------
        AQIForecast
            Forecast with predicted AQI values and confidence levels
        """
        if not sensor_data:
            return AQIForecast(
                location_lat=0.0,
                location_lng=0.0,
                generated_at=datetime.utcnow(),
                forecast_hours=hours,
            )

        # Get location from most recent data point
        latest = sensor_data[-1]
        current_aqi = latest.aqi

        # Calculate trend from historical data
        trend_factor = self._calculate_trend(sensor_data)

        # Calculate variability for confidence intervals
        variability = self._calculate_variability(sensor_data)

        # Generate forecast points
        forecast_points: List[ForecastDataPoint] = []
        now = datetime.utcnow()

        for i in range(1, hours // interval_hours + 1):
            forecast_time = now + timedelta(hours=i * interval_hours)

            # Apply trend factor (diminishes over time)
            time_decay = max(0.3, 1.0 - (i / (hours / interval_hours)) * 0.7)
            adjusted_trend = trend_factor * time_decay

            # Calculate predicted AQI
            predicted_aqi = round(current_aqi * (1 + adjusted_trend))
            predicted_aqi = max(0, min(500, predicted_aqi))  # Cap at 0-500

            # Calculate confidence (decreases with forecast distance)
            confidence = max(0.3, 1.0 - (i * 0.05))

            # Calculate min/max range based on variability
            range_margin = round(variability * (1 + i * 0.1))
            min_aqi = max(0, predicted_aqi - range_margin)
            max_aqi = min(500, predicted_aqi + range_margin)

            # Determine trend direction
            if adjusted_trend > 0.05:
                trend = "WORSENING"
            elif adjusted_trend < -0.05:
                trend = "IMPROVING"
            else:
                trend = "STABLE"

            forecast_points.append(
                ForecastDataPoint(
                    timestamp=forecast_time,
                    predicted_aqi=predicted_aqi,
                    confidence=round(confidence, 2),
                    min_aqi=min_aqi,
                    max_aqi=max_aqi,
                    trend=trend,
                )
            )

        return AQIForecast(
            location_lat=latest.timestamp.timestamp(),  # Placeholder
            location_lng=latest.timestamp.timestamp(),  # Placeholder
            generated_at=now,
            forecast_hours=hours,
            data_points=forecast_points,
        )

    def predict_with_pollutants(
        self,
        sensor_data: List[SensorDataPoint],
        hours: int = 24,
    ) -> AQIForecast:
        """Predict AQI with individual pollutant breakdown.

        Similar to predict_next_hours but considers individual pollutant
        trends for more accurate forecasting.

        Parameters
        ----------
        sensor_data:
            List of historical sensor data points
        hours:
            Number of hours to forecast

        Returns
        -------
        AQIForecast
            Forecast with predicted AQI values
        """
        # For now, delegate to the simpler method
        # Can be extended to track individual pollutant trends
        return self.predict_next_hours(sensor_data, hours)

    def _calculate_trend(self, sensor_data: List[SensorDataPoint]) -> float:
        """Calculate the AQI trend factor from historical data.

        Uses linear regression on recent data points to determine
        the rate of change.

        Parameters
        ----------
        sensor_data:
            List of historical sensor data points

        Returns
        -------
        float
            Trend factor (positive = worsening, negative = improving)
        """
        if len(sensor_data) < 2:
            return 0.0

        # Use last 6 data points for trend calculation
        recent_data = sensor_data[-6:] if len(sensor_data) >= 6 else sensor_data

        if len(recent_data) < 2:
            return 0.0

        # Simple linear trend: (last - first) / first / hours
        first_aqi = recent_data[0].aqi
        last_aqi = recent_data[-1].aqi

        if first_aqi == 0:
            return 0.0

        # Estimate hours between first and last reading
        time_diff = (recent_data[-1].timestamp - recent_data[0].timestamp).total_seconds() / 3600
        if time_diff == 0:
            return 0.0

        # Hourly rate of change
        hourly_change = (last_aqi - first_aqi) / first_aqi / time_diff

        return hourly_change

    def _calculate_variability(self, sensor_data: List[SensorDataPoint]) -> float:
        """Calculate AQI variability from historical data.

        Uses standard deviation to measure how much AQI fluctuates.

        Parameters
        ----------
        sensor_data:
            List of historical sensor data points

        Returns
        -------
        float
            Standard deviation of AQI values
        """
        if len(sensor_data) < 2:
            return 10.0  # Default variability

        # Use last 12 data points
        recent_data = sensor_data[-12:] if len(sensor_data) >= 12 else sensor_data

        if len(recent_data) < 2:
            return 10.0

        aqi_values = [dp.aqi for dp in recent_data]

        try:
            return stdev(aqi_values)
        except:
            return 10.0

    def get_forecast_summary(self, forecast: AQIForecast) -> Dict:
        """Get a summary of the forecast.

        Parameters
        ----------
        forecast:
            The forecast to summarize

        Returns
        -------
        dict
            Summary with key statistics and recommendations
        """
        if not forecast.data_points:
            return {
                "status": "NO_DATA",
                "message": "Unable to generate forecast",
            }

        avg_aqi = forecast.average_aqi
        max_aqi = forecast.max_aqi

        # Determine overall air quality outlook
        if max_aqi > 200:
            outlook = "POOR"
            recommendation = "Consider reducing outdoor activities during peak pollution hours."
        elif max_aqi > 100:
            outlook = "MODERATE"
            recommendation = "Sensitive groups should monitor air quality and limit prolonged outdoor exertion."
        else:
            outlook = "GOOD"
            recommendation = "Air quality is expected to be satisfactory."

        return {
            "status": "OK",
            "average_aqi": avg_aqi,
            "max_aqi": max_aqi,
            "overall_trend": forecast.overall_trend,
            "outlook": outlook,
            "recommendation": recommendation,
            "confidence": round(mean([dp.confidence for dp in forecast.data_points]), 2),
        }
