"""Unit tests for Threshold value object."""
import pytest

from src.domain.value_objects.threshold import Threshold
from src.domain.value_objects.severity import Severity


class TestThresholdCreation:
    """Tests for Threshold creation and validation."""

    def test_create_threshold_valid(self):
        """Test creating a valid threshold."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.warning == 35.0
        assert threshold.high == 55.0
        assert threshold.critical == 150.0

    def test_create_threshold_zero_warning_raises(self):
        """Test that zero warning threshold raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Threshold(warning=0.0, high=50.0, critical=100.0)

    def test_create_threshold_negative_warning_raises(self):
        """Test that negative warning threshold raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Threshold(warning=-10.0, high=50.0, critical=100.0)

    def test_create_threshold_high_below_warning_raises(self):
        """Test that high < warning raises ValueError."""
        with pytest.raises(ValueError, match=">= warning"):
            Threshold(warning=50.0, high=30.0, critical=100.0)

    def test_create_threshold_critical_below_high_raises(self):
        """Test that critical < high raises ValueError."""
        with pytest.raises(ValueError, match=">= high"):
            Threshold(warning=30.0, high=50.0, critical=40.0)

    def test_create_threshold_equal_values_allowed(self):
        """Test that equal threshold values are allowed."""
        threshold = Threshold(warning=50.0, high=50.0, critical=50.0)

        assert threshold.warning == 50.0
        assert threshold.high == 50.0
        assert threshold.critical == 50.0


class ThresholdCheckTests:
    """Tests for Threshold.check() method."""

    def test_check_below_warning_returns_none(self):
        """Test value below warning returns None."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.check(20.0) is None
        assert threshold.check(34.9) is None

    def test_check_at_warning_returns_warning(self):
        """Test value at warning threshold returns WARNING."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.check(35.0) == Severity.WARNING

    def test_check_between_warning_and_high_returns_warning(self):
        """Test value between warning and high returns WARNING."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.check(45.0) == Severity.WARNING

    def test_check_at_high_returns_high(self):
        """Test value at high threshold returns HIGH."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.check(55.0) == Severity.HIGH

    def test_check_between_high_and_critical_returns_high(self):
        """Test value between high and critical returns HIGH."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.check(100.0) == Severity.HIGH

    def test_check_at_critical_returns_critical(self):
        """Test value at critical threshold returns CRITICAL."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.check(150.0) == Severity.CRITICAL

    def test_check_above_critical_returns_critical(self):
        """Test value above critical threshold returns CRITICAL."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        assert threshold.check(200.0) == Severity.CRITICAL


class TestThresholdExceedancePercentage:
    """Tests for Threshold.exceedance_percentage() method."""

    def test_exceedance_below_warning_returns_zero(self):
        """Test exceedance for value below warning."""
        threshold = Threshold(warning=50.0, high=100.0, critical=150.0)

        assert threshold.exceedance_percentage(30.0) == 0.0

    def test_exceedance_at_warning_returns_zero(self):
        """Test exceedance for value at warning."""
        threshold = Threshold(warning=50.0, high=100.0, critical=150.0)

        assert threshold.exceedance_percentage(50.0) == 0.0

    def test_exceedance_above_warning(self):
        """Test exceedance percentage calculation."""
        threshold = Threshold(warning=50.0, high=100.0, critical=150.0)

        # 75 is 50% above 50
        assert threshold.exceedance_percentage(75.0) == 50.0

    def test_exceedance_double_warning(self):
        """Test exceedance when value is double the warning."""
        threshold = Threshold(warning=50.0, high=100.0, critical=150.0)

        # 100 is 100% above 50
        assert threshold.exceedance_percentage(100.0) == 100.0

    def test_exceedance_triple_warning(self):
        """Test exceedance when value is triple the warning."""
        threshold = Threshold(warning=50.0, high=100.0, critical=150.0)

        # 150 is 200% above 50
        assert threshold.exceedance_percentage(150.0) == 200.0


class TestThresholdSerialization:
    """Tests for Threshold serialization."""

    def test_to_dict(self):
        """Test converting threshold to dict."""
        threshold = Threshold(warning=35.0, high=55.0, critical=150.0)

        data = threshold.to_dict()

        assert data == {
            "warning": 35.0,
            "high": 55.0,
            "critical": 150.0,
        }

    def test_from_dict(self):
        """Test creating threshold from dict."""
        data = {"warning": 35.0, "high": 55.0, "critical": 150.0}

        threshold = Threshold.from_dict(data)

        assert threshold.warning == 35.0
        assert threshold.high == 55.0
        assert threshold.critical == 150.0

    def test_roundtrip_serialization(self):
        """Test roundtrip serialization."""
        original = Threshold(warning=40.0, high=80.0, critical=200.0)

        data = original.to_dict()
        restored = Threshold.from_dict(data)

        assert original == restored
