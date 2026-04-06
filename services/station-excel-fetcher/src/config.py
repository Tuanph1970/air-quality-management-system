"""Application configuration for station-excel-fetcher service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: Optional[str] = None) -> str:
    val = os.getenv(key, default)
    if val is None:
        raise ValueError(f"Required environment variable not set: {key}")
    return val


def _env_int(key: str, default: Optional[int] = None) -> int:
    val = os.getenv(key, str(default) if default is not None else "")
    return int(val) if val else (default or 0)


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


class Config:
    """All configuration for the station-excel-fetcher service."""

    # ── Service ──────────────────────────────────────────────────────────────
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "station-excel-fetcher")
    SERVICE_PORT: int = _env_int("SERVICE_PORT", 8011)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Paths ─────────────────────────────────────────────────────────────────
    # Root mount — the docker volume bind comes here
    MOUNT_ROOT: Path = Path(os.getenv("RAW_DATA_ROOT", "/app/raw_excel_data"))

    @property
    def output_dir(self) -> Path:
        """Directory where raw Excel files are saved."""
        d = self.MOUNT_ROOT / "raw"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def archive_dir(self) -> Path:
        """Directory for processed/archived Excel files."""
        d = self.MOUNT_ROOT / "processed"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def log_dir(self) -> Path:
        """Directory for fetch logs."""
        d = self.MOUNT_ROOT / "logs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ── Envisoft API ──────────────────────────────────────────────────────────
    ENVISOFT_BASE_URL: str = _env(
        "ENVISOFT_BASE_URL", "https://tw-envisoft.tedp.vn"
    )
    ENVISOFT_API_BASE_URL: str = _env(
        "ENVISOFT_API_BASE_URL", "https://admin-qttd.tedp.vn"
    )
    # Layer 1: HTTP Basic Auth
    ENVISOFT_BASIC_USER: str = _env("ENVISOFT_BASIC_USER", "tw-admin")
    ENVISOFT_BASIC_PASS: str = _env("ENVISOFT_BASIC_PASS", "tw-admin")
    # Layer 2: Web form login
    ENVISOFT_FORM_USER: str = _env("ENVISOFT_FORM_USER", "duongngocbach")
    ENVISOFT_FORM_PASS: str = _env("ENVISOFT_FORM_PASS", "1234567890!@#$%^&*()")

    # Data API endpoint (discovered via network interception)
    ENVISOFT_DATA_ENDPOINT: str = (
        f"{ENVISOFT_API_BASE_URL}/api/eos/data-average-by-time/exceed-by-time"
    )
    ENVISOFT_STATIONS_ENDPOINT: str = (
        f"{ENVISOFT_API_BASE_URL}/api/stations/search/"
        "findByStationTypeAndProvinceIdAndFtpConnectionStatusAndStatus"
        "AndUsingStatusAndStationNameAndTenantCode"
    )

    # Default fetch parameters
    ENVISOFT_STATION_TYPE: str = os.getenv("ENVISOFT_STATION_TYPE", "KK")  # KK=Air quality
    ENVISOFT_VIEW_TYPE: str = os.getenv("ENVISOFT_VIEW_TYPE", "hour")  # minute|hour|8hour|day|month
    ENVISOFT_PAGE_SIZE: int = _env_int("ENVISOFT_PAGE_SIZE", 200)

    # ── Scheduler ─────────────────────────────────────────────────────────────
    # Run at :01 of every hour (01:01, 02:01, ... 23:01)
    FETCH_CRON_EXPRESSION: str = os.getenv(
        "FETCH_CRON_EXPRESSION", "1 * * * *"
    )  # minute=1, every hour

    # Date range for each fetch (how many days back)
    FETCH_DAYS_BACK: int = _env_int("FETCH_DAYS_BACK", 2)

    # Maximum concurrent browser pages (for station pagination)
    MAX_PARALLEL_STATIONS: int = _env_int("MAX_PARALLEL_STATIONS", 5)

    # ── Dev / Debug ───────────────────────────────────────────────────────────
    # If True, uses cached cookies from envisoft_cookies.json instead of real login
    USE_CACHED_COOKIES: bool = _env_bool("USE_CACHED_COOKIES", False)
    COOKIES_CACHE_PATH: Path = Path(os.getenv(
        "COOKIES_CACHE_PATH",
        str(Path(__file__).parent.parent.parent.parent / "envisoft_cookies.json")
    ))

    # ── Startup Behaviour ──────────────────────────────────────────────────────
    # On startup, run a fetch immediately (for testing)
    FETCH_ON_STARTUP: bool = _env_bool("FETCH_ON_STARTUP", False)


config = Config()