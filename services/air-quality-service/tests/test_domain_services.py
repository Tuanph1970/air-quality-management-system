"""Tests for Air Quality Service domain layer.

Tests cover:
- AQI Calculator domain service
- Calibration Model ML service
- Cross-Validation service
- Data Fusion service
- Prediction service
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
from uuid import uuid4

from src.domain.services.aqi_calculator import AQICalculator, AQIResult
from src.domain.services.calibration_model import CalibrationModel, TrainingResult, EvaluationMetrics
from src.domain.services.cross_validator import CrossValidationService, ValidationResult
from src.domain.services.data_fusion import DataFusionService, FusedDataPoint
from src.domain.value_objects.location import Location
from src.domain.value_objects.aqi_category import get_category_for_aqi, get_all_categories


# =============================================================================
# AQI Calculator Tests
# =============================================================================

class TestAQICalculator:
    """Test the AQI calculation domain service."""

    @pytest.fixture
    def calculator(self):
        return AQICalculator()

    def test_calculate_single_pollutant(self, calculator):
        """Test AQI calculation for a single pollutant."""
        pollutants = {"pm25": 35.0}
        result = calculator.calculate_composite_aqi(pollutants)
        
        assert isinstance(result, AQIResult)
        assert result.aqi_value > 0
        assert result.aqi_value <= 500
        assert result.dominant_pollutant == "pm25"

    def test_calculate_multiple_pollutants(self, calculator):
        """Test composite AQI with multiple pollutants."""
        pollutants = {
            "pm25": 50.0,
            "pm10": 100.0,
            "o3": 0.05,
            "no2": 0.03,
        }
        result = calculator.calculate_composite_aqi(pollutants)
        
        assert result.aqi_value > 0
        assert result.dominant_pollutant in pollutants.keys()

    def test_calculate_empty_pollutants(self, calculator):
        """Test AQI calculation with no pollutant data."""
        pollutants = {}
        result = calculator.calculate_composite_aqi(pollutants)
        
        assert result.aqi_value == 0
        assert result.level.value == "Good"

    def test_aqi_categories(self):
        """Test AQI category retrieval."""
        categories = get_all_categories()
        assert len(categories) >= 6  # At least 6 AQI categories
        
        # Test specific category lookup
        good_category = get_category_for_aqi(25)
        assert good_category.level.value == "Good"
        
        hazardous_category = get_category_for_aqi(350)
        assert hazardous_category.level.value == "Hazardous"


# =============================================================================
# Calibration Model Tests
# =============================================================================

class TestCalibrationModel:
    """Test the ML calibration model."""

    @pytest.fixture
    def model(self, tmp_path):
        model_path = str(tmp_path / "test_model.joblib")
        return CalibrationModel(model_path=model_path)

    def test_calibrate_untrained(self, model):
        """Test calibration with untrained model returns raw values."""
        features = {
            "raw_pm25": 50.0,
            "raw_pm10": 100.0,
            "temperature": 25.0,
            "humidity": 60.0,
            "satellite_aod": 0.5,
            "hour": 12,
            "day_of_week": 0,
        }
        
        result = model.calibrate(features)
        
        # Untrained model should return raw values
        assert result["pm25"] == 50.0
        assert result["pm10"] == 100.0

    def test_train_model(self, model):
        """Test training the calibration model."""
        # Generate synthetic training data
        training_data = []
        for i in range(100):
            features = {
                "raw_pm25": np.random.uniform(10, 100),
                "raw_pm10": np.random.uniform(20, 200),
                "temperature": np.random.uniform(15, 35),
                "humidity": np.random.uniform(30, 80),
                "satellite_aod": np.random.uniform(0.1, 1.0),
                "hour": np.random.randint(0, 24),
                "day_of_week": np.random.randint(0, 7),
            }
            # Reference value with some noise
            reference = features["raw_pm25"] * np.random.uniform(0.9, 1.1)
            training_data.append((features, reference))

        result = model.train(training_data)
        
        assert isinstance(result, TrainingResult)
        assert result.r_squared >= 0
        assert result.r_squared <= 1
        assert result.training_samples == 100
        assert model.is_trained

    def test_calibrate_trained(self, model, tmp_path):
        """Test calibration with trained model."""
        # Train first
        training_data = []
        for i in range(100):
            features = {
                "raw_pm25": np.random.uniform(10, 100),
                "raw_pm10": np.random.uniform(20, 200),
                "temperature": np.random.uniform(15, 35),
                "humidity": np.random.uniform(30, 80),
                "satellite_aod": np.random.uniform(0.1, 1.0),
                "hour": 12,
                "day_of_week": 0,
            }
            reference = features["raw_pm25"] * np.random.uniform(0.9, 1.1)
            training_data.append((features, reference))
        
        model.train(training_data)
        
        # Now calibrate
        features = {
            "raw_pm25": 50.0,
            "raw_pm10": 100.0,
            "temperature": 25.0,
            "humidity": 60.0,
            "satellite_aod": 0.5,
            "hour": 12,
            "day_of_week": 0,
        }
        
        result = model.calibrate(features)
        
        # Trained model should return calibrated values (may differ from raw)
        assert "pm25" in result
        assert "pm10" in result

    def test_evaluate_model(self, model):
        """Test model evaluation."""
        # Train first
        training_data = []
        for i in range(100):
            features = {
                "raw_pm25": np.random.uniform(10, 100),
                "temperature": np.random.uniform(15, 35),
                "humidity": np.random.uniform(30, 80),
                "satellite_aod": np.random.uniform(0.1, 1.0),
                "hour": 12,
                "day_of_week": 0,
            }
            reference = features["raw_pm25"] * np.random.uniform(0.9, 1.1)
            training_data.append((features, reference))
        
        model.train(training_data)
        
        # Evaluate with test data
        test_data = []
        for i in range(20):
            features = {
                "raw_pm25": np.random.uniform(10, 100),
                "temperature": np.random.uniform(15, 35),
                "humidity": np.random.uniform(30, 80),
                "satellite_aod": np.random.uniform(0.1, 1.0),
                "hour": 12,
                "day_of_week": 0,
            }
            reference = features["raw_pm25"] * np.random.uniform(0.9, 1.1)
            test_data.append((features, reference))
        
        metrics = model.evaluate(test_data)
        
        assert isinstance(metrics, EvaluationMetrics)
        assert hasattr(metrics, 'r_squared')
        assert hasattr(metrics, 'rmse')
        assert hasattr(metrics, 'mae')


# =============================================================================
# Cross-Validation Service Tests
# =============================================================================

class TestCrossValidationService:
    """Test the cross-validation domain service."""

    @pytest.fixture
    def validator(self):
        return CrossValidationService()

    def test_validate_sensor_good_correlation(self, validator):
        """Test validation with good correlation."""
        sensor_id = uuid4()
        
        # Generate correlated sensor and satellite values
        np.random.seed(42)
        satellite_values = np.random.uniform(20, 80, 50)
        sensor_values = satellite_values * np.random.uniform(0.9, 1.1, 50)
        
        result = validator.validate_sensor(
            sensor_id=sensor_id,
            sensor_values=sensor_values.tolist(),
            satellite_values=satellite_values.tolist(),
        )
        
        assert isinstance(result, ValidationResult)
        assert result.sensor_id == sensor_id
        assert result.sample_count == 50
        assert result.correlation > 0.8  # Should have high correlation
        assert result.is_valid

    def test_validate_sensor_poor_correlation(self, validator):
        """Test validation with poor correlation."""
        sensor_id = uuid4()
        
        # Generate uncorrelated values
        np.random.seed(42)
        satellite_values = np.random.uniform(20, 80, 50)
        sensor_values = np.random.uniform(20, 80, 50)  # Independent
        
        result = validator.validate_sensor(
            sensor_id=sensor_id,
            sensor_values=sensor_values.tolist(),
            satellite_values=satellite_values.tolist(),
        )
        
        assert result.sample_count == 50
        assert result.correlation < 0.5  # Should have low correlation

    def test_validate_insufficient_data(self, validator):
        """Test validation with insufficient data."""
        sensor_id = uuid4()
        
        result = validator.validate_sensor(
            sensor_id=sensor_id,
            sensor_values=[50.0, 60.0],  # Only 2 samples
            satellite_values=[55.0, 58.0],
        )
        
        assert result.sample_count == 2
        assert not result.is_valid
        assert result.status == "insufficient_data"

    def test_detect_anomalies(self, validator):
        """Test anomaly detection."""
        readings = [50.0, 52.0, 48.0, 51.0, 200.0]  # Last one is anomalous
        
        anomalies = validator.detect_anomalies(readings, threshold=2.0)
        
        assert len(anomalies) >= 1
        assert 200.0 in [a.value for a in anomalies]


# =============================================================================
# Data Fusion Service Tests
# =============================================================================

class TestDataFusionService:
    """Test the data fusion domain service."""

    @pytest.fixture
    def calibration_model(self, tmp_path):
        model_path = str(tmp_path / "fusion_test_model.joblib")
        return CalibrationModel(model_path=model_path)

    @pytest.fixture
    def fusion_service(self, calibration_model):
        return DataFusionService(calibration_model)

    def test_fuse_data_both_sources(self, fusion_service):
        """Test fusion with both sensor and satellite data."""
        sensor_readings = [
            {
                "latitude": 10.7769,
                "longitude": 106.7009,
                "pm25": 50.0,
                "pm10": 100.0,
                "temperature": 25.0,
                "humidity": 60.0,
            }
        ]
        
        satellite_data = {
            "grid_cells": [
                {"lat": 10.78, "lon": 106.70, "value": 0.5},
            ]
        }
        
        timestamp = datetime.utcnow()
        
        fused_points = fusion_service.fuse_data(
            sensor_readings=sensor_readings,
            satellite_data=satellite_data,
            timestamp=timestamp,
        )
        
        assert len(fused_points) >= 1
        point = fused_points[0]
        
        assert isinstance(point, FusedDataPoint)
        assert point.sensor_pm25 == 50.0
        assert point.satellite_aod is not None
        assert point.fused_pm25 is not None
        assert point.confidence > 0
        assert "sensor" in point.data_sources
        assert "satellite" in point.data_sources

    def test_fuse_data_sensor_only(self, fusion_service):
        """Test fusion with sensor data only."""
        sensor_readings = [
            {
                "latitude": 10.7769,
                "longitude": 106.7009,
                "pm25": 50.0,
                "pm10": 100.0,
                "temperature": 25.0,
                "humidity": 60.0,
            }
        ]
        
        satellite_data = {"grid_cells": []}  # No satellite data
        
        timestamp = datetime.utcnow()
        
        fused_points = fusion_service.fuse_data(
            sensor_readings=sensor_readings,
            satellite_data=satellite_data,
            timestamp=timestamp,
        )
        
        assert len(fused_points) >= 1
        point = fused_points[0]
        
        assert point.sensor_pm25 == 50.0
        assert point.satellite_aod is None
        assert point.confidence < 0.9  # Lower confidence without satellite

    def test_fuse_data_satellite_only(self, fusion_service):
        """Test fusion with satellite data only (gap filling)."""
        sensor_readings = []  # No sensor data
        
        satellite_data = {
            "grid_cells": [
                {"lat": 10.78, "lon": 106.70, "value": 0.5},
            ]
        }
        
        timestamp = datetime.utcnow()
        
        fused_points = fusion_service.fuse_data(
            sensor_readings=sensor_readings,
            satellite_data=satellite_data,
            timestamp=timestamp,
        )
        
        # Should return empty or satellite-only points
        assert len(fused_points) == 0  # No sensors to fuse with


# =============================================================================
# Prediction Service Tests
# =============================================================================

class TestPredictionService:
    """Test the forecasting prediction service."""

    @pytest.fixture
    def prediction_service(self):
        from src.domain.services.prediction_service import PredictionService
        return PredictionService()

    def test_predict_next_hours(self, prediction_service):
        """Test AQI forecasting."""
        # Generate historical sensor data
        base_time = datetime.utcnow()
        sensor_data = []
        for i in range(24):
            sensor_data.append({
                "timestamp": base_time - timedelta(hours=i),
                "aqi": 50 + np.random.randint(-10, 10),
                "pm25": 30 + np.random.randint(-5, 5),
            })
        
        forecast = prediction_service.predict_next_hours(
            sensor_data=sensor_data,
            hours=24,
            interval_hours=1,
        )
        
        assert forecast is not None
        assert len(forecast.data_points) == 24
        assert all(dp.predicted_aqi >= 0 for dp in forecast.data_points)
        assert all(dp.predicted_aqi <= 500 for dp in forecast.data_points)

    def test_get_forecast_summary(self, prediction_service):
        """Test forecast summary generation."""
        # Generate forecast data points
        base_time = datetime.utcnow()
        data_points = []
        for i in range(24):
            data_points.append({
                "timestamp": base_time + timedelta(hours=i),
                "predicted_aqi": 50 + i,
                "min_aqi": 40 + i,
                "max_aqi": 60 + i,
                "confidence": 0.8,
            })
        
        forecast = type('Forecast', (), {
            'data_points': [type('DataPoint', (), dp)() for dp in data_points],
            'average_aqi': 62,
            'max_aqi': 74,
            'overall_trend': 'INCREASING',
        })()
        
        summary = prediction_service.get_forecast_summary(forecast)
        
        assert isinstance(summary, dict)
        assert "trend" in summary or "recommendation" in summary
