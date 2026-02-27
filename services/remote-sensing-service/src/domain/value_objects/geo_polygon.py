"""Geographic bounding box value object."""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class GeoPolygon:
    """Geographic bounding box — immutable value object."""

    north: float
    south: float
    east: float
    west: float

    def __post_init__(self):
        if not -90 <= self.south <= self.north <= 90:
            raise ValueError("Invalid latitude range")
        if not -180 <= self.west <= 180 or not -180 <= self.east <= 180:
            raise ValueError("Invalid longitude range")

    def contains(self, lat: float, lon: float) -> bool:
        return self.south <= lat <= self.north and self.west <= lon <= self.east

    def get_center(self) -> Tuple[float, float]:
        return ((self.north + self.south) / 2, (self.east + self.west) / 2)

    def to_dict(self) -> Dict:
        return {
            "north": self.north,
            "south": self.south,
            "east": self.east,
            "west": self.west,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GeoPolygon":
        return cls(
            north=data["north"],
            south=data["south"],
            east=data["east"],
            west=data["west"],
        )
