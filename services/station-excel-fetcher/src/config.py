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
        raise ValueError(f"Required env var not set: {key}")
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
    DEBUG: bool = _env_bool("DEBUG", False)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── MySQL Database ──────────────────────────────────────────────────────
    DATABASE_URL: str = _env(
        "DATABASE_URL",
        "mysql+aiomysql://root:Mysql_2026@mysql:3306/station_excel_fetcher_db",
    )

    # ── Paths ───────────────────────────────────────────────────────────────
    MOUNT_ROOT: Path = Path(os.getenv("RAW_DATA_ROOT", "/app/raw_excel_data"))

    @property
    def output_dir(self) -> Path:
        d = self.MOUNT_ROOT / "raw"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def archive_dir(self) -> Path:
        d = self.MOUNT_ROOT / "processed"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def log_dir(self) -> Path:
        d = self.MOUNT_ROOT / "logs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ── Envisoft Auth ───────────────────────────────────────────────────────
    ENVISOFT_BASE_URL: str = "https://tw-envisoft.tedp.vn"
    ENVISOFT_API_BASE_URL: str = "https://admin-qttd.tedp.vn"

    # Layer 1: HTTP Basic Auth
    ENVISOFT_BASIC_USER: str = os.getenv("ENVISOFT_BASIC_USER", "tw-admin")
    ENVISOFT_BASIC_PASS: str = os.getenv("ENVISOFT_BASIC_PASS", "tw-admin")

    # Layer 2: Web form login (inside iframe)
    ENVISOFT_FORM_USER: str = os.getenv("ENVISOFT_FORM_USER", "duongngocbach")
    ENVISOFT_FORM_PASS: str = os.getenv("ENVISOFT_FORM_PASS", "1234567890!@#$%^&*()")

    # ── Target Stations (5 stations) ──────────────────────────────────────
    TARGET_STATIONS: list[dict[str, str]] = [
        {
            "station_id": "32464751000956754854540602537",
            "name": "Station Tân Phú",
        },
        {
            "station_id": "32464751000956754854540602540",
            "name": "Station Quận 12",
        },
        {
            "station_id": "32464751000956754854540602541",
            "name": "Station Bình Tân",
        },
        {
            "station_id": "32481806597974747176167416654",
            "name": "Station Quận Thủ Đức",
        },
        {
            "station_id": "32481806690208467544715174761",
            "name": "Station Thành phố",
        },
    ]

    # ── Scheduler ───────────────────────────────────────────────────────────
    # Daily at 00:01 AM
    FETCH_CRON_EXPRESSION: str = os.getenv(
        "FETCH_CRON_EXPRESSION", "1 0 * * *"
    )

    # ── Startup Behaviour ───────────────────────────────────────────────────
    FETCH_ON_STARTUP: bool = _env_bool("FETCH_ON_STARTUP", False)


config = Config()