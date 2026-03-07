"""StationType value object - defines the classification of air quality stations."""
from __future__ import annotations

from enum import Enum


class StationType(str, Enum):
    """Station classification types.
    
    Attributes:
        GOVERNMENT: Government-operated environmental monitoring stations (e.g., EPA)
        INDUSTRIAL: Industrial facility monitoring stations
        URBAN: Urban area monitoring stations
        RURAL: Rural area monitoring stations
        TRAFFIC: Traffic/pollution hotspot monitoring stations
        BACKGROUND: Background air quality monitoring stations
    """
    
    GOVERNMENT = "GOVERNMENT"
    INDUSTRIAL = "INDUSTRIAL"
    URBAN = "URBAN"
    RURAL = "RURAL"
    TRAFFIC = "TRAFFIC"
    BACKGROUND = "BACKGROUND"
    
    @classmethod
    def from_string(cls, value: str) -> "StationType":
        """Create StationType from string value.
        
        Args:
            value: String representation of station type
            
        Returns:
            StationType enum member
            
        Raises:
            ValueError: If value is not a valid station type
        """
        try:
            return cls(value.upper())
        except ValueError:
            valid_types = [t.value for t in cls]
            raise ValueError(
                f"Invalid station type '{value}'. Valid types are: {', '.join(valid_types)}"
            )
