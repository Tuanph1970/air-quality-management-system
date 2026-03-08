"""Geographic bounding box value object."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BoundingBox:
    """Value Object - Geographic bounding box for simulation domain."""

    north: float
    south: float
    east: float
    west: float

    def __post_init__(self):
        """Validate bounding box coordinates."""
        if not -90 <= self.south <= 90:
            raise ValueError("South latitude must be between -90 and 90")
        if not -90 <= self.north <= 90:
            raise ValueError("North latitude must be between -90 and 90")
        if not -180 <= self.west <= 180:
            raise ValueError("West longitude must be between -180 and 180")
        if not -180 <= self.east <= 180:
            raise ValueError("East longitude must be between -180 and 180")
        if self.north <= self.south:
            raise ValueError("North must be greater than south")
        if self.east <= self.west:
            raise ValueError("East must be greater than west")

    @property
    def center_lat(self) -> float:
        """Calculate center latitude."""
        return (self.north + self.south) / 2

    @property
    def center_lon(self) -> float:
        """Calculate center longitude."""
        return (self.east + self.west) / 2

    @property
    def height_km(self) -> float:
        """Approximate height in kilometers."""
        return abs(self.north - self.south) * 111.0

    @property
    def width_km(self) -> float:
        """Approximate width in kilometers."""
        return abs(self.east - self.west) * 111.0 * abs(self.center_lat)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "north": self.north,
            "south": self.south,
            "east": self.east,
            "west": self.west,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "height_km": round(self.height_km, 2),
            "width_km": round(self.width_km, 2),
        }

    @classmethod
    def from_center_and_radius(
        cls, center_lat: float, center_lon: float, radius_km: float
    ) -> "BoundingBox":
        """Create bounding box from center point and radius."""
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(center_lat) if center_lat != 0 else 111.0)

        return cls(
            north=center_lat + lat_delta,
            south=center_lat - lat_delta,
            east=center_lon + lon_delta,
            west=center_lon - lon_delta,
        )
