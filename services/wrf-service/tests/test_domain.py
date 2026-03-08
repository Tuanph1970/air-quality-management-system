"""Tests for WRF domain entities."""
import pytest
from uuid import uuid4

from src.domain.entities.wrf_simulation import WRFSimulation, SimulationStatus
from src.domain.value_objects.bounding_box import BoundingBox
from src.domain.value_objects.wrf_config import WRFConfig, PhysicsOptions


class TestBoundingBox:
    """Tests for BoundingBox value object."""

    def test_create_valid_bounding_box(self):
        """Test creating a valid bounding box."""
        bbox = BoundingBox(
            north=21.5,
            south=20.5,
            east=106.0,
            west=105.5,
        )

        assert bbox.north == 21.5
        assert bbox.south == 20.5
        assert bbox.east == 106.0
        assert bbox.west == 105.5

    def test_center_coordinates(self):
        """Test center coordinate calculation."""
        bbox = BoundingBox(
            north=21.5,
            south=20.5,
            east=106.0,
            west=105.5,
        )

        assert bbox.center_lat == 21.0
        assert bbox.center_lon == 105.75

    def test_from_center_and_radius(self):
        """Test creating bounding box from center and radius."""
        bbox = BoundingBox.from_center_and_radius(
            center_lat=21.0,
            center_lon=105.75,
            radius_km=50,
        )

        assert abs(bbox.center_lat - 21.0) < 0.1
        assert abs(bbox.center_lon - 105.75) < 0.1

    def test_invalid_north_greater_than_90(self):
        """Test validation fails when north > 90."""
        with pytest.raises(ValueError):
            BoundingBox(north=91, south=20, east=106, west=105)

    def test_invalid_north_less_than_south(self):
        """Test validation fails when north <= south."""
        with pytest.raises(ValueError):
            BoundingBox(north=20, south=21, east=106, west=105)


class TestWRFConfig:
    """Tests for WRFConfig value object."""

    def test_create_valid_config(self, sample_bounding_box):
        """Test creating a valid WRF configuration."""
        config = WRFConfig(
            bounding_box=sample_bounding_box,
            horizontal_resolution_km=9.0,
            vertical_levels=30,
            simulation_hours=48,
        )

        assert config.horizontal_resolution_km == 9.0
        assert config.vertical_levels == 30
        assert config.simulation_hours == 48

    def test_invalid_resolution_too_fine(self, sample_bounding_box):
        """Test validation fails when resolution is too fine."""
        with pytest.raises(ValueError):
            WRFConfig(
                bounding_box=sample_bounding_box,
                horizontal_resolution_km=0.5,  # Too fine
                vertical_levels=30,
                simulation_hours=48,
            )

    def test_estimated_grid_points(self, sample_bounding_box):
        """Test grid point estimation."""
        config = WRFConfig(
            bounding_box=sample_bounding_box,
            horizontal_resolution_km=9.0,
            vertical_levels=30,
            simulation_hours=48,
        )

        assert config.estimated_grid_points > 0

    def test_to_dict(self, sample_config):
        """Test converting config to dictionary."""
        config_dict = sample_config.to_dict()

        assert "bounding_box" in config_dict
        assert "horizontal_resolution_km" in config_dict
        assert "vertical_levels" in config_dict
        assert "simulation_hours" in config_dict


class TestWRFSimulation:
    """Tests for WRFSimulation entity."""

    def test_create_simulation(self, sample_config):
        """Test creating a new simulation."""
        simulation = WRFSimulation.create(
            name="Test Simulation",
            config=sample_config,
        )

        assert simulation.name == "Test Simulation"
        assert simulation.status == SimulationStatus.PENDING
        assert simulation.progress_percent == 0
        assert len(simulation.collect_events()) > 0

    def test_start_simulation(self, sample_config):
        """Test starting a simulation."""
        simulation = WRFSimulation.create(
            name="Test Simulation",
            config=sample_config,
        )

        simulation.start("/app/data/gfs/test")

        assert simulation.status == SimulationStatus.DOWNLOADING_DATA
        assert simulation.gfs_data_path == "/app/data/gfs/test"

    def test_cannot_start_already_started(self, sample_config):
        """Test cannot start a simulation that's already started."""
        simulation = WRFSimulation.create(
            name="Test Simulation",
            config=sample_config,
        )
        simulation.start("/app/data/gfs/test")

        with pytest.raises(ValueError):
            simulation.start("/app/data/gfs/test2")

    def test_update_progress(self, sample_config):
        """Test updating simulation progress."""
        simulation = WRFSimulation.create(
            name="Test Simulation",
            config=sample_config,
        )

        simulation.update_progress(
            SimulationStatus.RUNNING,
            50,
            "Processing...",
        )

        assert simulation.status == SimulationStatus.RUNNING
        assert simulation.progress_percent == 50

    def test_mark_completed(self, sample_config):
        """Test marking simulation as completed."""
        simulation = WRFSimulation.create(
            name="Test Simulation",
            config=sample_config,
        )

        simulation.mark_completed(
            "/app/data/output",
            ["/app/data/output/wrfout_d01"],
        )

        assert simulation.status == SimulationStatus.COMPLETED
        assert simulation.progress_percent == 100
        assert simulation.output_file_path == "/app/data/output"

    def test_mark_failed(self, sample_config):
        """Test marking simulation as failed."""
        simulation = WRFSimulation.create(
            name="Test Simulation",
            config=sample_config,
        )

        simulation.mark_failed("Test error")

        assert simulation.status == SimulationStatus.FAILED
        assert simulation.error_message == "Test error"

    def test_to_dict(self, sample_config):
        """Test converting simulation to dictionary."""
        simulation = WRFSimulation.create(
            name="Test Simulation",
            config=sample_config,
        )

        sim_dict = simulation.to_dict()

        assert sim_dict["id"] is not None
        assert sim_dict["name"] == "Test Simulation"
        assert sim_dict["status"] == "pending"
        assert "config" in sim_dict
