"""GeographicCoordinate value object - represents GPS coordinates."""
from __future__ import annotations

from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Optional


@dataclass(frozen=True)
class GeographicCoordinate:
    """Immutable value object representing geographic coordinates.
    
    Attributes:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
        altitude: Optional altitude in meters above sea level
    
    Example:
        >>> coord = GeographicCoordinate(latitude=21.0285, longitude=105.8542)
        >>> coord.latitude
        21.0285
    """
    
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    
    def __post_init__(self):
        """Validate coordinate ranges."""
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(
                f"Latitude must be between -90 and 90, got {self.latitude}"
            )
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(
                f"Longitude must be between -180 and 180, got {self.longitude}"
            )
        if self.altitude is not None and self.altitude < -500:
            raise ValueError(
                f"Altitude seems invalid: {self.altitude} meters"
            )
    
    @classmethod
    def create(
        cls,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
    ) -> "GeographicCoordinate":
        """Factory method to create coordinates.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            altitude: Optional altitude in meters
            
        Returns:
            New GeographicCoordinate instance
        """
        return cls(latitude=latitude, longitude=longitude, altitude=altitude)
    
    def distance_to(self, other: "GeographicCoordinate") -> float:
        """Calculate distance to another coordinate using Haversine formula.
        
        Args:
            other: Another GeographicCoordinate to calculate distance to
            
        Returns:
            Distance in kilometers
        """
        R = 6371.0  # Earth's radius in kilometers
        
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary with latitude, longitude, and altitude
        """
        result = {"latitude": self.latitude, "longitude": self.longitude}
        if self.altitude is not None:
            result["altitude"] = self.altitude
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "GeographicCoordinate":
        """Create from dictionary representation.
        
        Args:
            data: Dictionary with latitude, longitude, and optional altitude
            
        Returns:
            New GeographicCoordinate instance
        """
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"],
            altitude=data.get("altitude"),
        )
    
    def __str__(self) -> str:
        """String representation of coordinates."""
        lat_dir = "N" if self.latitude >= 0 else "S"
        lon_dir = "E" if self.longitude >= 0 else "W"
        return f"{abs(self.latitude):.4f}°{lat_dir}, {abs(self.longitude):.4f}°{lon_dir}"
