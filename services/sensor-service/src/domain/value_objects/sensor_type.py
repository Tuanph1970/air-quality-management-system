"""Sensor type enum."""
from enum import Enum


class SensorType(str, Enum):
    PM25 = "PM25"
    PM10 = "PM10"
    CO = "CO"
    NO2 = "NO2"
    SO2 = "SO2"
    O3 = "O3"
    MULTI = "MULTI"
