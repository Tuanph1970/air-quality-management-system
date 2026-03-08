"""Configuration for WRF Service."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class WRFSettings:
    """WRF Service configuration settings."""

    # Service settings
    SERVICE_NAME: str = "wrf-service"
    SERVICE_PORT: int = 8009
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # WRF data paths
    WRF_DATA_DIR: str = "/app/data"
    GFS_DATA_DIR: str = "/app/data/gfs"
    WRF_OUTPUT_DIR: str = "/app/data/wrf_output"
    WPS_DIR: str = "/app/wrf/WPS"
    WRF_MODEL_DIR: str = "/app/wrf/WRFV4"

    # GFS download settings
    GFS_SOURCE_URL: str = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
    GFS_MAX_FORECAST_HOURS: int = 120
    GFS_DOWNLOAD_TIMEOUT: int = 300  # seconds

    # WRF execution settings
    WRF_NUM_PROCESSES: int = 4
    WRF_MEMORY_PER_PROCESS_MB: int = 2048
    WRF_EXECUTION_TIMEOUT_HOURS: int = 24

    # Simulation defaults
    DEFAULT_RESOLUTION_KM: float = 9.0
    DEFAULT_VERTICAL_LEVELS: int = 30
    DEFAULT_SIMULATION_HOURS: int = 48

    # External services
    AIR_QUALITY_SERVICE_URL: Optional[str] = None
    SENSOR_SERVICE_URL: Optional[str] = None

    @classmethod
    def from_env(cls) -> "WRFSettings":
        """Create settings from environment variables."""
        return cls(
            SERVICE_NAME=os.getenv("SERVICE_NAME", "wrf-service"),
            SERVICE_PORT=int(os.getenv("SERVICE_PORT", "8009")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            DEBUG=os.getenv("DEBUG", "False").lower() == "true",
            WRF_DATA_DIR=os.getenv("WRF_DATA_DIR", "/app/data"),
            GFS_DATA_DIR=os.getenv("GFS_DATA_DIR", "/app/data/gfs"),
            WRF_OUTPUT_DIR=os.getenv("WRF_OUTPUT_DIR", "/app/data/wrf_output"),
            WPS_DIR=os.getenv("WPS_DIR", "/app/wrf/WPS"),
            WRF_MODEL_DIR=os.getenv("WRF_MODEL_DIR", "/app/wrf/WRFV4"),
            GFS_MAX_FORECAST_HOURS=int(
                os.getenv("GFS_MAX_FORECAST_HOURS", "120")
            ),
            WRF_NUM_PROCESSES=int(os.getenv("WRF_NUM_PROCESSES", "4")),
            AIR_QUALITY_SERVICE_URL=os.getenv("AIR_QUALITY_SERVICE_URL"),
            SENSOR_SERVICE_URL=os.getenv("SENSOR_SERVICE_URL"),
        )


settings = WRFSettings.from_env()
