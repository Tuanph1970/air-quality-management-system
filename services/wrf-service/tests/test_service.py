"""Tests for WRF service."""
import pytest

from src.domain.services.wrf_simulation_service import WRFSimulationService
from src.domain.value_objects.bounding_box import BoundingBox
from src.domain.value_objects.wrf_config import WRFConfig


class TestWRFSimulationService:
    """Tests for WRF simulation domain service."""

    def test_validate_valid_config(self, sample_config):
        """Test validating a valid configuration."""
        service = WRFSimulationService()
        is_valid, error_message = service.validate_simulation_config(
            sample_config
        )

        assert is_valid is True
        assert error_message is None

    def test_validate_domain_too_large(self):
        """Test validation fails for domain that's too large."""
        service = WRFSimulationService()
        large_bbox = BoundingBox.from_center_and_radius(
            center_lat=21.0,
            center_lon=105.75,
            radius_km=3000,  # Very large
        )

        config = WRFConfig(
            bounding_box=large_bbox,
            horizontal_resolution_km=9.0,
            vertical_levels=30,
            simulation_hours=48,
        )

        is_valid, error_message = service.validate_simulation_config(config)
        assert is_valid is False
        assert "exceeds maximum" in error_message

    def test_estimate_runtime(self, sample_config):
        """Test runtime estimation."""
        service = WRFSimulationService()
        runtime_hours = service.estimate_runtime_hours(sample_config)

        assert runtime_hours > 0
        assert runtime_hours < 100  # Should be reasonable

    def test_recommend_configuration(self):
        """Test configuration recommendation."""
        service = WRFSimulationService()

        config = service.recommend_configuration(
            center_lat=21.0,
            center_lon=105.75,
            region_radius_km=100,
            available_memory_gb=16,
            max_runtime_hours=4,
        )

        assert config is not None
        assert config.horizontal_resolution_km >= 3
        assert config.vertical_levels >= 20
