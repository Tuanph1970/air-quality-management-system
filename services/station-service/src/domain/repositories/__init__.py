"""Domain repositories for the station service."""
from __future__ import annotations

from .station_repository import StationRepository
from .reading_repository import ReadingRepository

__all__ = ["StationRepository", "ReadingRepository"]
