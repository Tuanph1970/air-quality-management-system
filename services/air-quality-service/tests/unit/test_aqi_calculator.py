"""Unit tests for AQI Calculator domain service."""
import pytest

from src.domain.services.aqi_calculator import AQICalculator, AQIResult
from src.domain.value_objects.aqi_level import AQILevel


class TestAQICalculatorSinglePollutant:
    """Tests for calculate_aqi() with single pollutants."""

    def test_calculate_pm25_good(self):
        """Test PM2.5 AQI in Good range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm25", 10.0)
        
        assert 0 <= aqi <= 50

    def test_calculate_pm25_moderate(self):
        """Test PM2.5 AQI in Moderate range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm25", 25.0)
        
        assert 51 <= aqi <= 100

    def test_calculate_pm25_unhealthy_sensitive(self):
        """Test PM2.5 AQI in Unhealthy for Sensitive Groups range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm25", 45.0)
        
        assert 101 <= aqi <= 150

    def test_calculate_pm25_unhealthy(self):
        """Test PM2.5 AQI in Unhealthy range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm25", 100.0)
        
        assert 151 <= aqi <= 200

    def test_calculate_pm25_very_unhealthy(self):
        """Test PM2.5 AQI in Very Unhealthy range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm25", 200.0)
        
        assert 201 <= aqi <= 300

    def test_calculate_pm25_hazardous(self):
        """Test PM2.5 AQI in Hazardous range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm25", 350.0)
        
        assert 301 <= aqi <= 500

    def test_calculate_pm10_good(self):
        """Test PM10 AQI in Good range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm10", 40.0)
        
        assert 0 <= aqi <= 50

    def test_calculate_co_moderate(self):
        """Test CO AQI in Moderate range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("co", 6.0)
        
        assert 51 <= aqi <= 100

    def test_calculate_o3_good(self):
        """Test O3 AQI in Good range."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("o3", 80.0)
        
        assert 0 <= aqi <= 50

    def test_calculate_unknown_pollutant_raises(self):
        """Test that unknown pollutant raises ValueError."""
        calc = AQICalculator()
        
        with pytest.raises(ValueError, match="Unknown pollutant"):
            calc.calculate_aqi("unknown", 100.0)

    def test_calculate_negative_concentration_raises(self):
        """Test that negative concentration raises ValueError."""
        calc = AQICalculator()
        
        with pytest.raises(ValueError, match="non-negative"):
            calc.calculate_aqi("pm25", -10.0)

    def test_calculate_exceeds_max_breakpoint(self):
        """Test AQI calculation for concentration exceeding max breakpoint."""
        calc = AQICalculator()
        aqi = calc.calculate_aqi("pm25", 600.0)
        
        assert aqi == 500  # Capped at 500


class TestAQICalculatorComposite:
    """Tests for calculate_composite_aqi()."""

    def test_calculate_composite_single_pollutant(self):
        """Test composite AQI with single pollutant."""
        calc = AQICalculator()
        result = calc.calculate_composite_aqi({"pm25": 35.0})
        
        assert isinstance(result, AQIResult)
        assert result.dominant_pollutant == "pm25"
        assert 0 <= result.aqi_value <= 500

    def test_calculate_composite_multiple_pollutants(self):
        """Test composite AQI with multiple pollutants."""
        calc = AQICalculator()
        pollutants = {
            "pm25": 35.0,
            "pm10": 50.0,
            "o3": 60.0,
        }
        result = calc.calculate_composite_aqi(pollutants)
        
        # Dominant pollutant should be the one with highest AQI
        assert result.dominant_pollutant in pollutants.keys()
        
        # Verify individual AQIs are calculated
        individual = calc.get_all_pollutant_aqis(pollutants)
        assert "pm25" in individual
        assert "pm10" in individual
        assert "o3" in individual

    def test_calculate_composite_empty_pollutants(self):
        """Test composite AQI with empty pollutants dict."""
        calc = AQICalculator()
        result = calc.calculate_composite_aqi({})
        
        assert result.aqi_value == 0
        assert result.level == AQILevel.GOOD
        assert result.dominant_pollutant == "none"

    def test_calculate_composite_all_categories(self):
        """Test composite AQI returns all category information."""
        calc = AQICalculator()
        result = calc.calculate_composite_aqi({"pm25": 100.0})
        
        assert result.aqi_value > 0
        assert result.level in AQILevel
        assert result.category
        assert result.color.startswith("#")
        assert result.health_message
        assert result.caution_message


class TestAQICalculatorCategory:
    """Tests for AQI category methods."""

    def test_get_aqi_category_good(self):
        """Test category lookup for Good AQI."""
        calc = AQICalculator()
        category = calc.get_aqi_category(25)
        
        assert "GOOD" in category

    def test_get_aqi_category_moderate(self):
        """Test category lookup for Moderate AQI."""
        calc = AQICalculator()
        category = calc.get_aqi_category(75)
        
        assert "MODERATE" in category

    def test_get_aqi_category_unhealthy(self):
        """Test category lookup for Unhealthy AQI."""
        calc = AQICalculator()
        category = calc.get_aqi_category(175)
        
        assert "UNHEALTHY" in category

    def test_get_aqi_category_hazardous(self):
        """Test category lookup for Hazardous AQI."""
        calc = AQICalculator()
        category = calc.get_aqi_category(400)
        
        assert "HAZARDOUS" in category

    def test_get_aqi_color(self):
        """Test color code retrieval."""
        calc = AQICalculator()
        
        # Green for Good
        assert calc.get_aqi_color(25).startswith("#")
        # Red for Unhealthy
        assert calc.get_aqi_color(175).startswith("#")

    def test_get_health_message(self):
        """Test health message retrieval."""
        calc = AQICalculator()
        
        message = calc.get_health_message(150)
        assert len(message) > 0
        assert "health" in message.lower() or "effect" in message.lower()

    def test_get_caution_message(self):
        """Test caution message retrieval."""
        calc = AQICalculator()
        
        message = calc.get_caution_message(150)
        assert isinstance(message, str)
