"""Test fixtures for WRF Service."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.value_objects.bounding_box import BoundingBox
from src.domain.value_objects.wrf_config import WRFConfig, PhysicsOptions
from src.domain.entities.wrf_simulation import WRFSimulation, SimulationStatus
from src.infrastructure.external.gfs_data_downloader import GFSDataDownloader
from src.infrastructure.wrf.wrf_model_runner import WRFModelRunner


@pytest.fixture
def sample_bounding_box():
    """Create a sample bounding box for Hanoi region."""
    return BoundingBox(
        north=21.5,
        south=20.5,
        east=106.0,
        west=105.5,
    )


@pytest.fixture
def sample_config(sample_bounding_box):
    """Create a sample WRF configuration."""
    return WRFConfig(
        bounding_box=sample_bounding_box,
        horizontal_resolution_km=9.0,
        vertical_levels=30,
        simulation_hours=48,
        physics_options=PhysicsOptions(),
    )


@pytest.fixture
def sample_simulation(sample_config):
    """Create a sample WRF simulation."""
    return WRFSimulation.create(
        name="Test Simulation",
        config=sample_config,
    )


@pytest.fixture
def mock_gfs_downloader():
    """Create a mock GFS downloader."""
    downloader = AsyncMock(spec=GFSDataDownloader)
    downloader.download.return_value = "/app/data/gfs/test-simulation"
    downloader.download_sample_data.return_value = "/app/data/gfs/test-simulation"
    return downloader


@pytest.fixture
def mock_wrf_runner():
    """Create a mock WRF runner."""
    runner = AsyncMock(spec=WRFModelRunner)
    runner.run_preprocessing = AsyncMock()
    runner.run_simulation = AsyncMock(return_value=["/app/data/wrf_output/wrfout_d01"])
    runner.post_process = AsyncMock()
    return runner


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])
    repo.save = AsyncMock(side_effect=lambda x: x)
    repo.delete = AsyncMock(return_value=True)
    repo.get_active_simulations = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
