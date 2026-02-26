"""Location value object.

Represents a geographic coordinate pair with validation and distance
calculation.  Immutable by design (frozen dataclass).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt


_EARTH_RADIUS_KM = 6_371.0


@dataclass(frozen=True)
class Location:
    """Immutable geographic coordinate (WGS-84).

    Raises ``ValueError`` on construction if coordinates are out of range.
    """

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise ValueError(
                f"Latitude must be between -90 and 90, got {self.latitude}"
            )
        if not -180 <= self.longitude <= 180:
            raise ValueError(
                f"Longitude must be between -180 and 180, got {self.longitude}"
            )

    def distance_to(self, other: Location) -> float:
        """Calculate the great-circle distance to *other* in kilometres.

        Uses the Haversine formula for accuracy on a spherical Earth
        (mean radius 6 371 km).
        """
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return _EARTH_RADIUS_KM * c
