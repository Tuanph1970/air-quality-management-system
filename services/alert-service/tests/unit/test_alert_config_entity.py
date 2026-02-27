"""Unit tests for AlertConfig entity."""
import pytest
from uuid import uuid4

from src.domain.entities.alert_config import AlertConfig
from src.domain.value_objects.threshold import Threshold


class TestAlertConfigCreate:
    """Tests for AlertConfig.create() factory method."""

    def test_create_alert_config_success(self, sample_alert_config_data):
        """Test creating an alert config with valid data."""
        config = AlertConfig.create(**sample_alert_config_data)

        assert config.id is not None
        assert config.name == sample_alert_config_data["name"]
        assert config.pollutant == sample_alert_config_data["pollutant"]
        assert config.warning_threshold == sample_alert_config_data["warning_threshold"]
        assert config.high_threshold == sample_alert_config_data["high_threshold"]
        assert config.critical_threshold == sample_alert_config_data["critical_threshold"]
        assert config.is_active is True
        assert config.notify_email is True
        assert config.notify_sms is False

    def test_create_alert_config_validates_threshold_order(self):
        """Test that thresholds must be ordered: warning < high < critical."""
        with pytest.raises(ValueError, match="threshold"):
            AlertConfig.create(
                name="Invalid Config",
                pollutant="pm25",
                warning_threshold=100.0,  # Too high
                high_threshold=50.0,
                critical_threshold=150.0,
            )

    def test_create_alert_config_negative_duration_raises(self):
        """Test that negative duration_minutes raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            AlertConfig.create(
                name="PM2.5 Config",
                pollutant="pm25",
                warning_threshold=35.0,
                high_threshold=55.0,
                critical_threshold=150.0,
                duration_minutes=-10,
            )

    def test_create_alert_config_default_values(self):
        """Test default values for optional fields."""
        config = AlertConfig.create(
            name="CO Config",
            pollutant="co",
            warning_threshold=5.0,
            high_threshold=10.0,
            critical_threshold=30.0,
        )

        assert config.duration_minutes == 0
        assert config.notify_email is True
        assert config.notify_sms is False
        assert config.is_active is True


class TestAlertConfigUpdate:
    """Tests for AlertConfig.update() method."""

    def test_update_name(self, sample_alert_config):
        """Test updating the name."""
        sample_alert_config.update(name="Updated PM2.5 Limit")
        assert sample_alert_config.name == "Updated PM2.5 Limit"

    def test_update_thresholds_validates_order(self, sample_alert_config):
        """Test that updating thresholds validates ordering."""
        with pytest.raises(ValueError, match="threshold"):
            sample_alert_config.update(
                warning_threshold=200.0,  # Invalid: higher than high
            )

    def test_update_duration_minutes(self, sample_alert_config):
        """Test updating duration_minutes."""
        sample_alert_config.update(duration_minutes=15)
        assert sample_alert_config.duration_minutes == 15

    def test_update_negative_duration_raises(self, sample_alert_config):
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            sample_alert_config.update(duration_minutes=-5)

    def test_update_notification_settings(self, sample_alert_config):
        """Test updating notification settings."""
        sample_alert_config.update(notify_email=False, notify_sms=True)
        assert sample_alert_config.notify_email is False
        assert sample_alert_config.notify_sms is True

    def test_update_partial_fields(self, sample_alert_config):
        """Test that only specified fields are updated."""
        original_name = sample_alert_config.name
        original_pollutant = sample_alert_config.pollutant

        sample_alert_config.update(notify_sms=True)

        assert sample_alert_config.name == original_name
        assert sample_alert_config.pollutant == original_pollutant
        assert sample_alert_config.notify_sms is True

    def test_update_updates_timestamp(self, sample_alert_config):
        """Test that update changes updated_at timestamp."""
        original_updated = sample_alert_config.updated_at
        sample_alert_config.update(name="New Name")
        assert sample_alert_config.updated_at > original_updated


class TestAlertConfigActivateDeactivate:
    """Tests for AlertConfig activate/deactivate methods."""

    def test_activate_config(self, sample_alert_config):
        """Test activating a config."""
        sample_alert_config.deactivate()
        assert sample_alert_config.is_active is False

        sample_alert_config.activate()
        assert sample_alert_config.is_active is True

    def test_deactivate_config(self, sample_alert_config):
        """Test deactivating a config."""
        sample_alert_config.deactivate()
        assert sample_alert_config.is_active is False

    def test_activate_updates_timestamp(self, sample_alert_config):
        """Test that activate changes updated_at timestamp."""
        sample_alert_config.deactivate()
        original_updated = sample_alert_config.updated_at
        sample_alert_config.activate()
        assert sample_alert_config.updated_at > original_updated


class TestAlertConfigToThreshold:
    """Tests for AlertConfig.to_threshold() method."""

    def test_to_threshold_returns_value_object(self, sample_alert_config):
        """Test that to_threshold returns a Threshold value object."""
        threshold = sample_alert_config.to_threshold()

        assert isinstance(threshold, Threshold)
        assert threshold.warning == sample_alert_config.warning_threshold
        assert threshold.high == sample_alert_config.high_threshold
        assert threshold.critical == sample_alert_config.critical_threshold


class TestAlertConfigProperties:
    """Tests for AlertConfig query properties."""

    def test_config_for_different_pollutants(self):
        """Test creating configs for different pollutants."""
        pollutants = ["pm25", "pm10", "co", "no2", "so2", "o3"]

        configs = {}
        for pollutant in pollutants:
            configs[pollutant] = AlertConfig.create(
                name=f"{pollutant.upper()} Limit",
                pollutant=pollutant,
                warning_threshold=30.0,
                high_threshold=50.0,
                critical_threshold=100.0,
            )

        for p in pollutants:
            assert configs[p].pollutant == p
