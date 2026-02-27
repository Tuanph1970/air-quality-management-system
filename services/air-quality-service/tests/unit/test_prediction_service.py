"""Unit tests for Prediction Service domain service."""
import pytest
from datetime import datetime, timedelta

from src.domain.services.prediction_service import (
    PredictionService,
    SensorDataPoint,
    AQIForecast,
    ForecastDataPoint,
)


class TestPredictionServicePredict:
    """Tests for predict_next_hours()."""

    def test_predict_next_hours_basic(self):
        """Test basic forecast generation."""
        service = PredictionService()
        
        now = datetime.utcnow()
        sensor_data = [
            SensorDataPoint(
                timestamp=now - timedelta(hours=i),
                pollutants={"pm25": 30 + i},
                aqi=50 + i * 2,
            )
            for i in range(6, 0, -1)
        ]
        
        forecast = service.predict_next_hours(sensor_data, hours=24)
        
        assert isinstance(forecast, AQIForecast)
        assert forecast.forecast_hours == 24
        assert len(forecast.data_points) > 0

    def test_predict_next_hours_empty_data(self):
        """Test forecast with empty sensor data."""
        service = PredictionService()
        
        forecast = service.predict_next_hours([], hours=24)
        
        assert isinstance(forecast, AQIForecast)
        assert len(forecast.data_points) == 0
        assert forecast.forecast_hours == 24

    def test_predict_next_hours_single_datapoint(self):
        """Test forecast with single data point."""
        service = PredictionService()
        
        sensor_data = [
            SensorDataPoint(
                timestamp=datetime.utcnow(),
                pollutants={"pm25": 35.0},
                aqi=75,
            )
        ]
        
        forecast = service.predict_next_hours(sensor_data, hours=12)
        
        assert isinstance(forecast, AQIForecast)
        # Should still generate forecast points
        assert len(forecast.data_points) > 0

    def test_predict_next_hours_interval(self):
        """Test forecast with custom interval."""
        service = PredictionService()
        
        now = datetime.utcnow()
        sensor_data = [
            SensorDataPoint(
                timestamp=now - timedelta(hours=i),
                pollutants={"pm25": 30},
                aqi=50,
            )
            for i in range(6, 0, -1)
        ]
        
        forecast = service.predict_next_hours(sensor_data, hours=24, interval_hours=3)
        
        # 24 hours / 3 hour interval = 8 data points
        assert len(forecast.data_points) == 8

    def test_forecast_aqi_capped(self):
        """Test that forecasted AQI is capped at 0-500."""
        service = PredictionService()
        
        now = datetime.utcnow()
        # Create data with increasing trend
        sensor_data = [
            SensorDataPoint(
                timestamp=now - timedelta(hours=i),
                pollutants={"pm25": 100 + i * 50},
                aqi=200 + i * 50,
            )
            for i in range(6, 0, -1)
        ]
        
        forecast = service.predict_next_hours(sensor_data, hours=168)  # 1 week
        
        for point in forecast.data_points:
            assert 0 <= point.predicted_aqi <= 500
            assert 0 <= point.min_aqi <= 500
            assert 0 <= point.max_aqi <= 500

    def test_forecast_confidence_decreases(self):
        """Test that forecast confidence decreases over time."""
        service = PredictionService()
        
        now = datetime.utcnow()
        sensor_data = [
            SensorDataPoint(
                timestamp=now - timedelta(hours=i),
                pollutants={"pm25": 35},
                aqi=75,
            )
            for i in range(6, 0, -1)
        ]
        
        forecast = service.predict_next_hours(sensor_data, hours=48, interval_hours=1)
        
        if len(forecast.data_points) >= 2:
            # First point should have higher confidence than last
            first_confidence = forecast.data_points[0].confidence
            last_confidence = forecast.data_points[-1].confidence
            assert first_confidence >= last_confidence

    def test_forecast_trend_direction(self):
        """Test trend detection in forecast."""
        service = PredictionService()
        
        now = datetime.utcnow()
        
        # Improving trend (decreasing AQI)
        improving_data = [
            SensorDataPoint(
                timestamp=now - timedelta(hours=i),
                pollutants={"pm25": 100 - i * 10},
                aqi=150 - i * 15,
            )
            for i in range(6, 0, -1)
        ]
        
        forecast = service.predict_next_hours(improving_data, hours=24)
        
        # Check that trend is detected
        trends = [dp.trend for dp in forecast.data_points]
        assert any(t in ["IMPROVING", "STABLE", "WORSENING"] for t in trends)


class TestPredictionServiceForecastProperties:
    """Tests for AQIForecast properties."""

    def test_forecast_average_aqi(self):
        """Test average AQI calculation."""
        forecast = AQIForecast(
            location_lat=21.0,
            location_lng=105.0,
            generated_at=datetime.utcnow(),
            forecast_hours=24,
            data_points=[
                ForecastDataPoint(
                    timestamp=datetime.utcnow() + timedelta(hours=i),
                    predicted_aqi=50 + i * 10,
                    min_aqi=40 + i * 10,
                    max_aqi=60 + i * 10,
                    confidence=0.9 - i * 0.05,
                    trend="STABLE",
                )
                for i in range(5)
            ],
        )
        
        # Average of [50, 60, 70, 80, 90] = 70
        assert forecast.average_aqi == 70

    def test_forecast_max_aqi(self):
        """Test max AQI calculation."""
        forecast = AQIForecast(
            location_lat=21.0,
            location_lng=105.0,
            generated_at=datetime.utcnow(),
            forecast_hours=24,
            data_points=[
                ForecastDataPoint(
                    timestamp=datetime.utcnow() + timedelta(hours=i),
                    predicted_aqi=50 + i * 20,
                    min_aqi=40,
                    max_aqi=60,
                    confidence=0.9,
                    trend="WORSENING",
                )
                for i in range(5)
            ],
        )
        
        # Max of [50, 70, 90, 110, 130] = 130
        assert forecast.max_aqi == 130

    def test_forecast_overall_trend(self):
        """Test overall trend calculation."""
        # Worsening trend
        forecast_worsening = AQIForecast(
            location_lat=21.0,
            location_lng=105.0,
            generated_at=datetime.utcnow(),
            forecast_hours=24,
            data_points=[
                ForecastDataPoint(
                    timestamp=datetime.utcnow() + timedelta(hours=i),
                    predicted_aqi=50 + i * 20,
                    min_aqi=40,
                    max_aqi=60,
                    confidence=0.9,
                    trend="WORSENING",
                )
                for i in range(6)
            ],
        )
        
        assert forecast_worsening.overall_trend == "WORSENING"

    def test_forecast_empty_data_points(self):
        """Test forecast with empty data points."""
        forecast = AQIForecast(
            location_lat=21.0,
            location_lng=105.0,
            generated_at=datetime.utcnow(),
            forecast_hours=24,
            data_points=[],
        )
        
        assert forecast.average_aqi == 0
        assert forecast.max_aqi == 0
        assert forecast.overall_trend == "STABLE"


class TestPredictionServiceSummary:
    """Tests for get_forecast_summary()."""

    def test_get_forecast_summary_good(self):
        """Test summary for good air quality forecast."""
        service = PredictionService()
        
        forecast = AQIForecast(
            location_lat=21.0,
            location_lng=105.0,
            generated_at=datetime.utcnow(),
            forecast_hours=24,
            data_points=[
                ForecastDataPoint(
                    timestamp=datetime.utcnow() + timedelta(hours=i),
                    predicted_aqi=30,
                    min_aqi=20,
                    max_aqi=40,
                    confidence=0.9,
                    trend="STABLE",
                )
                for i in range(5)
            ],
        )
        
        summary = service.get_forecast_summary(forecast)
        
        assert summary["status"] == "OK"
        assert summary["outlook"] == "GOOD"

    def test_get_forecast_summary_poor(self):
        """Test summary for poor air quality forecast."""
        service = PredictionService()
        
        forecast = AQIForecast(
            location_lat=21.0,
            location_lng=105.0,
            generated_at=datetime.utcnow(),
            forecast_hours=24,
            data_points=[
                ForecastDataPoint(
                    timestamp=datetime.utcnow() + timedelta(hours=i),
                    predicted_aqi=250,
                    min_aqi=200,
                    max_aqi=300,
                    confidence=0.7,
                    trend="WORSENING",
                )
                for i in range(5)
            ],
        )
        
        summary = service.get_forecast_summary(forecast)
        
        assert summary["status"] == "OK"
        assert summary["outlook"] == "POOR"

    def test_get_forecast_summary_no_data(self):
        """Test summary with no forecast data."""
        service = PredictionService()
        
        forecast = AQIForecast(
            location_lat=21.0,
            location_lng=105.0,
            generated_at=datetime.utcnow(),
            forecast_hours=24,
            data_points=[],
        )
        
        summary = service.get_forecast_summary(forecast)
        
        assert summary["status"] == "NO_DATA"
