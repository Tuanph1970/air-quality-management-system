"""Pollutant value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Pollutant:
    """Value Object for a pollutant measurement."""

    name: str
    value: float
    unit: str = "ug/m3"
