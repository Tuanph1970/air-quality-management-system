"""Sensor service application queries."""
from .get_readings_query import GetReadingAverageQuery, GetReadingsQuery
from .get_sensor_query import GetSensorQuery, ListSensorsQuery

__all__ = [
    "GetReadingAverageQuery",
    "GetReadingsQuery",
    "GetSensorQuery",
    "ListSensorsQuery",
]
