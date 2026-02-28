"""Tests for Sensor Service domain layer.

Tests cover:
- Sensor entity
- Reading entity
- Value objects (SensorType, SensorStatus, CalibrationParams)
- AQI Calculator domain service
- Sensor repository operations
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import numpy as np

from src.domain.entities.sensor import Sensor
from src.domain.entities.reading import Reading
from src.domain.value_objects.sensor_type import SensorType
from src.domain.value_objects.sensor_status import SensorStatus
from src.domain.value_objects.calibration_params import CalibrationParams
from src.domain.services.aqi_calculator import AQICalculator


# =============================================================================
# Value Object Tests
# =============================================================================

class TestSensorType:
    """Test SensorType value object."""

    def test_sensor_type_values(self):
        """Test sensor type enum values."""
        assert SensorType.LOW_COST_PM.value == "low_cost_pm"
        assert SensorType.REFERENCE_STATION.value == "reference_station"
        assert SensorType.MULTI_GAS.value == "multi_gas"

    def test_sensor_type_from_string(self):
        """Test creating sensor type from string."""
        sensor_type = SensorType("low_cost_pm")
        assert sensor_type == SensorType.LOW_COST_PM

    def test_invalid_sensor_type(self):
        """Test that invalid sensor type raises error."""
        with pytest.raises(ValueError):
            SensorType("invalid_type")


class TestSensorStatus:
    """Test SensorStatus value object."""

    def test_sensor_status_values(self):
        """Test sensor status enum values."""
        assert SensorStatus.ONLINE.value == "online"
        assert SensorStatus.OFFLINE.value == "offline"
        assert SensorStatus.CALIBRATING.value == "calibrating"


class TestCalibrationParams:
    """Test CalibrationParams value object."""

    def test_create_calibration_params(self):
        """Test creating calibration parameters."""
        params = CalibrationParams(
            pm25_slope=1.05,
            pm25_intercept=2.0,
            pm25_r_squared=0.92,
            pm10_slope=0.98,
            pm10_intercept=1.5,
            pm10_r_squared=0.89,
        )
        
        assert params.pm25_slope == 1.05
        assert params.pm25_r_squared == 0.92
        assert params.is_valid() is True

    def test_invalid_calibration_params(self):
        """Test that invalid params are detected."""
        params = CalibrationParams(
            pm25_slope=1.0,
            pm25_intercept=0.0,
            pm25_r_squared=0.3,  # Low R²
        )
        
        assert params.is_valid() is False

    def test_calibrate_value(self):
        """Test calibration calculation."""
        params = CalibrationParams(
            pm25_slope=1.05,
            pm25_intercept=2.0,
            pm25_r_squared=0.92,
        )
        
        raw_value = 50.0
        calibrated = params.calibrate_value(raw_value, "pm25")
        
        expected = raw_value * 1.05 + 2.0
        assert calibrated == expected


# =============================================================================
# Entity Tests
# =============================================================================

class TestSensor:
    """Test Sensor entity."""

    def test_create_sensor(self):
        """Test creating a sensor entity."""
        sensor = Sensor.create(
            serial_number="SN-001",
            sensor_type=SensorType.LOW_COST_PM,
            model="AirQuality-Pro",
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
        )
        
        assert isinstance(sensor.id, UUID)
        assert sensor.serial_number == "SN-001"
        assert sensor.sensor_type == SensorType.LOW_COST_PM
        assert sensor.status == SensorStatus.ONLINE
        assert sensor.is_active() is True

    def test_sensor_calibration(self):
        """Test sensor calibration update."""
        sensor = Sensor.create(
            serial_number="SN-001",
            sensor_type=SensorType.LOW_COST_PM,
            model="AirQuality-Pro",
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
        )
        
        params = CalibrationParams(
            pm25_slope=1.05,
            pm25_intercept=2.0,
            pm25_r_squared=0.92,
        )
        
        sensor.calibrate(params)
        
        assert sensor.calibration_params is not None
        assert sensor.calibration_params.pm25_slope == 1.05

    def test_sensor_status_update(self):
        """Test sensor status update."""
        sensor = Sensor.create(
            serial_number="SN-001",
            sensor_type=SensorType.LOW_COST_PM,
            model="AirQuality-Pro",
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
        )
        
        assert sensor.status == SensorStatus.ONLINE
        
        sensor.update_status(SensorStatus.OFFLINE)
        
        assert sensor.status == SensorStatus.OFFLINE
        assert sensor.is_active() is False

    def test_apply_calibration_to_reading(self):
        """Test applying calibration to a reading."""
        sensor = Sensor.create(
            serial_number="SN-001",
            sensor_type=SensorType.LOW_COST_PM,
            model="AirQuality-Pro",
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
        )
        
        params = CalibrationParams(
            pm25_slope=1.05,
            pm25_intercept=2.0,
            pm25_r_squared=0.92,
        )
        sensor.calibrate(params)
        
        raw_pm25 = 50.0
        calibrated = sensor.apply_calibration(raw_pm25, "pm25")
        
        expected = raw_pm25 * 1.05 + 2.0
        assert calibrated == expected


class TestReading:
    """Test Reading entity."""

    def test_create_reading(self):
        """Test creating a sensor reading."""
        reading = Reading.create(
            sensor_id=uuid4(),
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
            pm25=35.0,
            pm10=60.0,
            temperature=28.5,
            humidity=65.0,
        )
        
        assert isinstance(reading.id, UUID)
        assert reading.pm25 == 35.0
        assert reading.pm10 == 60.0
        assert reading.aqi > 0

    def test_reading_aqi_calculation(self):
        """Test AQI calculation in reading."""
        reading = Reading.create(
            sensor_id=uuid4(),
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
            pm25=50.0,
            pm10=100.0,
        )
        
        assert reading.aqi > 0
        assert reading.aqi <= 500

    def test_reading_validation(self):
        """Test reading validation."""
        # Valid reading
        reading = Reading.create(
            sensor_id=uuid4(),
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
            pm25=35.0,
            pm10=60.0,
        )
        
        assert reading.is_valid() is True
        
        # Invalid reading (negative value)
        invalid_reading = Reading.create(
            sensor_id=uuid4(),
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
            pm25=-10.0,  # Invalid
            pm10=60.0,
        )
        
        assert invalid_reading.is_valid() is False


# =============================================================================
# Domain Service Tests
# =============================================================================

class TestAQICalculator:
    """Test AQI Calculator domain service."""

    @pytest.fixture
    def calculator(self):
        return AQICalculator()

    def test_calculate_pm25_aqi_good(self, calculator):
        """Test PM2.5 AQI in Good range."""
        aqi = calculator.calculate_pm25_aqi(10.0)
        
        assert aqi >= 0
        assert aqi <= 50

    def test_calculate_pm25_aqi_moderate(self, calculator):
        """Test PM2.5 AQI in Moderate range."""
        aqi = calculator.calculate_pm25_aqi(25.0)
        
        assert aqi > 50
        assert aqi <= 100

    def test_calculate_pm25_aqi_unhealthy_sg(self, calculator):
        """Test PM2.5 AQI in Unhealthy for Sensitive Groups range."""
        aqi = calculator.calculate_pm25_aqi(55.0)
        
        assert aqi > 100
        assert aqi <= 150

    def test_calculate_pm25_aqi_unhealthy(self, calculator):
        """Test PM2.5 AQI in Unhealthy range."""
        aqi = calculator.calculate_pm25_aqi(150.0)
        
        assert aqi > 150
        assert aqi <= 200

    def test_calculate_pm25_aqi_very_unhealthy(self, calculator):
        """Test PM2.5 AQI in Very Unhealthy range."""
        aqi = calculator.calculate_pm25_aqi(250.0)
        
        assert aqi > 200
        assert aqi <= 300

    def test_calculate_pm25_aqi_hazardous(self, calculator):
        """Test PM2.5 AQI in Hazardous range."""
        aqi = calculator.calculate_pm25_aqi(350.0)
        
        assert aqi > 300
        assert aqi <= 500

    def test_calculate_pm10_aqi(self, calculator):
        """Test PM10 AQI calculation."""
        aqi = calculator.calculate_pm10_aqi(100.0)
        
        assert aqi >= 0
        assert aqi <= 500

    def test_get_dominant_pollutant(self, calculator):
        """Test dominant pollutant identification."""
        pollutant = calculator.get_dominant_pollutant({"pm25": 100, "pm10": 50})
        assert pollutant == "pm25"
        
        pollutant = calculator.get_dominant_pollutant({"pm25": 50, "pm10": 100})
        assert pollutant == "pm10"

    def test_get_health_recommendations(self, calculator):
        """Test health recommendations generation."""
        recommendations = calculator.get_health_recommendations(aqi=75)
        
        assert isinstance(recommendations, dict)
        assert "general_population" in recommendations or "health_message" in recommendations


# =============================================================================
# Integration Tests
# =============================================================================

class TestSensorReadingIntegration:
    """Integration tests for sensor reading workflow."""

    def test_full_sensor_workflow(self):
        """Test complete sensor reading workflow."""
        factory_id = uuid4()
        
        # Create sensor
        sensor = Sensor.create(
            serial_number="SN-001",
            sensor_type=SensorType.LOW_COST_PM,
            model="AirQuality-Pro",
            factory_id=factory_id,
            latitude=10.7769,
            longitude=106.7009,
        )
        
        assert sensor.is_active() is True
        
        # Calibrate sensor
        params = CalibrationParams(
            pm25_slope=1.05,
            pm25_intercept=2.0,
            pm25_r_squared=0.92,
        )
        sensor.calibrate(params)
        
        # Create reading
        reading = Reading.create(
            sensor_id=sensor.id,
            factory_id=factory_id,
            latitude=sensor.latitude,
            longitude=sensor.longitude,
            pm25=50.0,
            pm10=100.0,
            temperature=28.5,
            humidity=65.0,
        )
        
        # Apply calibration
        calibrated_pm25 = sensor.apply_calibration(reading.pm25, "pm25")
        assert calibrated_pm25 > reading.pm25  # Due to slope > 1
        
        # Validate reading
        assert reading.is_valid() is True
        
        # Check AQI
        assert reading.aqi > 0
        assert reading.aqi <= 500

    def test_sensor_with_multiple_readings(self):
        """Test sensor with multiple readings over time."""
        sensor = Sensor.create(
            serial_number="SN-001",
            sensor_type=SensorType.LOW_COST_PM,
            factory_id=uuid4(),
            latitude=10.7769,
            longitude=106.7009,
        )
        
        readings = []
        base_time = datetime.utcnow()
        
        for i in range(24):
            reading = Reading.create(
                sensor_id=sensor.id,
                factory_id=sensor.factory_id,
                latitude=sensor.latitude,
                longitude=sensor.longitude,
                pm25=30 + np.random.randint(-10, 20),
                pm10=50 + np.random.randint(-15, 30),
                temperature=25 + np.random.randint(-3, 5),
                humidity=60 + np.random.randint(-10, 15),
            )
            reading.timestamp = base_time - timedelta(hours=i)
            readings.append(reading)
        
        # Calculate statistics
        pm25_values = [r.pm25 for r in readings]
        avg_pm25 = sum(pm25_values) / len(pm25_values)
        
        assert avg_pm25 > 0
        assert len(readings) == 24
