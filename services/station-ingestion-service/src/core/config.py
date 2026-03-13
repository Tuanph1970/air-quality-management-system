"""Configuration for station ingestion service."""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Service configuration."""

    # Service
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8008"))

    # External Station API
    STATION_API_BASE_URL: str = os.getenv(
        "STATION_API_BASE_URL", "https://admin-qttd.tedp.vn/api/partner/v1"
    )
    STATION_API_KEY: str = os.getenv(
        "STATION_API_KEY", "c9e03048-46e1-40b0-9b6b-f12accef9f5a"
    )

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/station_ingestion_db"
    )

    # Data fetching
    FETCH_INTERVAL_SECONDS: int = int(os.getenv("FETCH_INTERVAL_SECONDS", "300"))  # 5 minutes
    AQI_HOURS_PAGE_SIZE: int = int(os.getenv("AQI_HOURS_PAGE_SIZE", "100"))

    # Fake data mode (for development/testing when external API is unavailable)
    USE_FAKE_DATA: bool = os.getenv("USE_FAKE_DATA", "False").lower() in ("true", "1", "yes")

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls()


config = Config.from_env()
