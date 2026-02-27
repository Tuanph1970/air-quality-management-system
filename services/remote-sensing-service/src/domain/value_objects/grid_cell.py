"""Satellite grid cell value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GridCell:
    """Single grid cell with satellite value — immutable value object."""

    lat: float
    lon: float
    value: float
    uncertainty: float = 0.0

    def __post_init__(self):
        if not -90 <= self.lat <= 90:
            raise ValueError("Invalid latitude")
        if not -180 <= self.lon <= 180:
            raise ValueError("Invalid longitude")
