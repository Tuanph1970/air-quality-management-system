"""Sensor service domain repository interfaces."""
from .reading_repository import ReadingRepository
from .sensor_repository import SensorRepository

__all__ = ["ReadingRepository", "SensorRepository"]
