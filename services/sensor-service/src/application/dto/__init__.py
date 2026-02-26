"""Sensor service data transfer objects."""
from .reading_dto import ReadingDTO, ReadingListDTO
from .sensor_dto import SensorDTO, SensorListDTO

__all__ = [
    "ReadingDTO",
    "ReadingListDTO",
    "SensorDTO",
    "SensorListDTO",
]
