"""Data quality validator - domain service for validating station readings."""
from __future__ import annotations

from typing import Dict, Optional, Tuple
from ..value_objects.pollutant_type import PollutantType


class DataQualityValidator:
    """Domain service for validating air quality reading data.
    
    Provides validation rules for pollutant readings to ensure data quality.
    Uses realistic upper bounds based on typical air quality measurements.
    
    Example:
        >>> validator = DataQualityValidator()
        >>> validator.validate_reading(PollutantType.PM25, 35.5)
        (True, None)
        >>> validator.validate_reading(PollutantType.PM25, -5.0)
        (False, "Value cannot be negative")
    """
    
    # Realistic maximum values for pollutants (upper bounds for validation)
    # These are extremely high values that would indicate sensor errors
    MAX_VALUES: Dict[PollutantType, float] = {
        PollutantType.SO2: 1000.0,   # µg/m³ - Very high pollution
        PollutantType.NOX: 500.0,    # µg/m³
        PollutantType.NO2: 400.0,    # µg/m³
        PollutantType.CO: 50.0,      # mg/m³
        PollutantType.CO2: 5000.0,   # ppm (indoor can be high)
        PollutantType.PM25: 500.0,   # µg/m³ - Hazardous level
        PollutantType.PM10: 1000.0,  # µg/m³
        PollutantType.O3: 300.0,     # µg/m³
    }
    
    # Minimum expected values (typically 0, but some pollutants have background levels)
    MIN_VALUES: Dict[PollutantType, float] = {
        PollutantType.SO2: 0.0,
        PollutantType.NOX: 0.0,
        PollutantType.NO2: 0.0,
        PollutantType.CO: 0.0,
        PollutantType.CO2: 300.0,    # ppm - atmospheric baseline
        PollutantType.PM25: 0.0,
        PollutantType.PM10: 0.0,
        PollutantType.O3: 0.0,
    }
    
    # Plausibility checks between related pollutants
    # PM2.5 should typically be <= PM10
    RELATED_CHECKS = [
        ("PM25", "PM10", lambda pm25, pm10: pm25 <= pm10 * 1.1),  # 10% tolerance
    ]
    
    def validate_reading(
        self,
        pollutant_type: PollutantType,
        value: float,
    ) -> Tuple[bool, Optional[str]]:
        """Validate a single pollutant reading.
        
        Args:
            pollutant_type: Type of pollutant
            value: Measured value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value < 0:
            return False, "Value cannot be negative"
        
        min_val = self.MIN_VALUES.get(pollutant_type, 0.0)
        max_val = self.MAX_VALUES.get(pollutant_type)
        
        if value < min_val:
            return False, f"Value {value} below minimum {min_val} for {pollutant_type.value}"
        
        if max_val is not None and value > max_val:
            return False, f"Value {value} exceeds maximum {max_val} for {pollutant_type.value}"
        
        return True, None
    
    def validate_readings_batch(
        self,
        readings: Dict[str, float],
    ) -> Tuple[bool, Optional[str]]:
        """Validate a batch of readings from a station.
        
        Args:
            readings: Dictionary mapping pollutant names to values
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate individual readings
        for pollutant_str, value in readings.items():
            try:
                pollutant_type = PollutantType.from_string(pollutant_str)
            except ValueError:
                continue  # Skip unknown pollutants
            
            is_valid, error = self.validate_reading(pollutant_type, value)
            if not is_valid:
                return False, error
        
        # Check plausibility relationships
        for pollutant1, pollutant2, check_func in self.RELATED_CHECKS:
            if pollutant1 in readings and pollutant2 in readings:
                if not check_func(readings[pollutant1], readings[pollutant2]):
                    return False, (
                        f"Implausible relationship: {pollutant1}={readings[pollutant1]} "
                        f"vs {pollutant2}={readings[pollutant2]}"
                    )
        
        return True, None
    
    def get_quality_flag(
        self,
        pollutant_type: PollutantType,
        value: float,
    ) -> str:
        """Determine quality flag for a reading.
        
        Args:
            pollutant_type: Type of pollutant
            value: Measured value
            
        Returns:
            Quality flag: 'GOOD', 'SUSPECT', or 'BAD'
        """
        max_val = self.MAX_VALUES.get(pollutant_type, float('inf'))
        
        if value < 0:
            return "BAD"
        
        if value > max_val:
            return "BAD"
        
        # Flag as suspect if value is in extreme range (>80% of max)
        if value > max_val * 0.8:
            return "SUSPECT"
        
        return "GOOD"
    
    @classmethod
    def get_pollutant_info(cls, pollutant_type: PollutantType) -> dict:
        """Get information about a pollutant.
        
        Args:
            pollutant_type: Type of pollutant
            
        Returns:
            Dictionary with pollutant information
        """
        return {
            "name": pollutant_type.value,
            "unit": pollutant_type.unit,
            "min": cls.MIN_VALUES.get(pollutant_type, 0.0),
            "max": cls.MAX_VALUES.get(pollutant_type),
            "who_guideline": pollutant_type.who_guideline,
        }
