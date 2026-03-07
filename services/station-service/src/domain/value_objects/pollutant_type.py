"""PollutantType value object - defines air quality pollutants."""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class PollutantType(str, Enum):
    """Air pollutant types monitored by stations.
    
    Attributes:
        SO2: Sulfur Dioxide (µg/m³)
        NOX: Nitrogen Oxides (µg/m³)
        NO2: Nitrogen Dioxide (µg/m³)
        CO: Carbon Monoxide (mg/m³)
        CO2: Carbon Dioxide (ppm)
        PM25: Particulate Matter ≤2.5µm (µg/m³)
        PM10: Particulate Matter ≤10µm (µg/m³)
        O3: Ozone (µg/m³)
    """
    
    SO2 = "SO2"
    NOX = "NOX"
    NO2 = "NO2"
    CO = "CO"
    CO2 = "CO2"
    PM25 = "PM25"
    PM10 = "PM10"
    O3 = "O3"
    
    @classmethod
    def from_string(cls, value: str) -> "PollutantType":
        """Create PollutantType from string value.
        
        Args:
            value: String representation of pollutant type
            
        Returns:
            PollutantType enum member
            
        Raises:
            ValueError: If value is not a valid pollutant type
        """
        try:
            return cls(value.upper())
        except ValueError:
            valid_types = [p.value for p in cls]
            raise ValueError(
                f"Invalid pollutant type '{value}'. Valid types are: {', '.join(valid_types)}"
            )
    
    @property
    def unit(self) -> str:
        """Get the measurement unit for this pollutant.
        
        Returns:
            Unit string (e.g., 'µg/m³', 'mg/m³', 'ppm')
        """
        units = {
            PollutantType.SO2: "µg/m³",
            PollutantType.NOX: "µg/m³",
            PollutantType.NO2: "µg/m³",
            PollutantType.CO: "mg/m³",
            PollutantType.CO2: "ppm",
            PollutantType.PM25: "µg/m³",
            PollutantType.PM10: "µg/m³",
            PollutantType.O3: "µg/m³",
        }
        return units[self]
    
    @property
    def who_guideline(self) -> Optional[float]:
        """Get WHO Air Quality Guideline value (2021).
        
        Returns:
            WHO guideline value or None if not available
        """
        guidelines = {
            PollutantType.SO2: 40.0,  # 24-hour mean
            PollutantType.NOX: None,  # NOX not directly specified
            PollutantType.NO2: 25.0,  # 24-hour mean
            PollutantType.CO: None,   # CO has different guideline structure
            PollutantType.CO2: None,  # Not typically in WHO AQG
            PollutantType.PM25: 15.0, # 24-hour mean
            PollutantType.PM10: 45.0, # 24-hour mean
            PollutantType.O3: 100.0,  # 8-hour mean
        }
        return guidelines.get(self)


@dataclass(frozen=True)
class PollutantReading:
    """Immutable value object representing a single pollutant reading.
    
    Attributes:
        pollutant_type: Type of pollutant measured
        value: Measured concentration value
        unit: Unit of measurement (auto-derived from pollutant_type)
    """
    
    pollutant_type: PollutantType
    value: float
    
    def __post_init__(self):
        """Validate the reading value."""
        if self.value < 0:
            raise ValueError(f"Pollutant reading value cannot be negative: {self.value}")
    
    @classmethod
    def create(cls, pollutant_type: str | PollutantType, value: float) -> "PollutantReading":
        """Factory method to create a PollutantReading.
        
        Args:
            pollutant_type: Pollutant type as string or enum
            value: Measured value
            
        Returns:
            New PollutantReading instance
        """
        if isinstance(pollutant_type, str):
            pollutant_type = PollutantType.from_string(pollutant_type)
        return cls(pollutant_type=pollutant_type, value=value)
