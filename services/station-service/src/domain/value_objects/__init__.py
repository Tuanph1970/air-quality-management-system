"""Value objects for the station domain."""
from __future__ import annotations

from .station_type import StationType
from .pollutant_type import PollutantType
from .geographic_coordinate import GeographicCoordinate

__all__ = ["StationType", "PollutantType", "GeographicCoordinate"]
