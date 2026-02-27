"""Unit tests for Severity value object."""
import pytest

from src.domain.value_objects.severity import Severity


class TestSeverityFromExceedance:
    """Tests for Severity.from_exceedance() factory method."""

    def test_warning_for_small_exceedance(self):
        """Test WARNING for 1-49% exceedance."""
        assert Severity.from_exceedance(1.0) == Severity.WARNING
        assert Severity.from_exceedance(25.0) == Severity.WARNING
        assert Severity.from_exceedance(49.9) == Severity.WARNING

    def test_high_for_medium_exceedance(self):
        """Test HIGH for 50-99% exceedance."""
        assert Severity.from_exceedance(50.0) == Severity.HIGH
        assert Severity.from_exceedance(75.0) == Severity.HIGH
        assert Severity.from_exceedance(99.0) == Severity.HIGH

    def test_critical_for_large_exceedance(self):
        """Test CRITICAL for 100%+ exceedance."""
        assert Severity.from_exceedance(100.0) == Severity.CRITICAL
        assert Severity.from_exceedance(150.0) == Severity.CRITICAL
        assert Severity.from_exceedance(500.0) == Severity.CRITICAL

    def test_zero_exceedance_raises(self):
        """Test that 0% exceedance raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Severity.from_exceedance(0.0)

    def test_negative_exceedance_raises(self):
        """Test that negative exceedance raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Severity.from_exceedance(-10.0)


class TestSeverityProperties:
    """Tests for Severity query properties."""

    def test_is_critical_for_critical(self):
        """Test is_critical for CRITICAL severity."""
        assert Severity.CRITICAL.is_critical is True
        assert Severity.WARNING.is_critical is False
        assert Severity.HIGH.is_critical is False

    def test_should_notify_sms(self):
        """Test should_notify_sms property."""
        assert Severity.WARNING.should_notify_sms is False
        assert Severity.HIGH.should_notify_sms is True
        assert Severity.CRITICAL.should_notify_sms is True

    def test_numeric_level(self):
        """Test numeric_level property ordering."""
        assert Severity.WARNING.numeric_level == 1
        assert Severity.HIGH.numeric_level == 2
        assert Severity.CRITICAL.numeric_level == 3
        assert Severity.WARNING.numeric_level < Severity.HIGH.numeric_level
        assert Severity.HIGH.numeric_level < Severity.CRITICAL.numeric_level


class TestSeverityStringComparison:
    """Tests for Severity string comparison (str Enum)."""

    def test_severity_equals_string(self):
        """Test that Severity equals string value."""
        assert Severity.WARNING == "WARNING"
        assert Severity.HIGH == "HIGH"
        assert Severity.CRITICAL == "CRITICAL"

    def test_string_equals_severity(self):
        """Test that string equals Severity value."""
        assert "WARNING" == Severity.WARNING
        assert "HIGH" == Severity.HIGH
        assert "CRITICAL" == Severity.CRITICAL

    def test_severity_in_list(self):
        """Test Severity membership in string list."""
        assert Severity.WARNING in ["WARNING", "HIGH", "CRITICAL"]
        assert "WARNING" in [Severity.WARNING, Severity.HIGH, Severity.CRITICAL]
