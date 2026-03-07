"""PollutantReading entity - represents a time-series air quality reading."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID, uuid4

from ..value_objects.pollutant_type import PollutantType


@dataclass
class PollutantReading:
    """Entity representing a single pollutant measurement from a station.
    
    This is a time-series entity that stores individual pollutant readings.
    Multiple readings are typically recorded together as a batch from a station.
    
    Attributes:
        id: Unique identifier
        station_id: Reference to the station
        pollutant_type: Type of pollutant measured
        value: Measured concentration
        unit: Unit of measurement
        quality_flag: Optional quality indicator (GOOD, SUSPECT, BAD)
        timestamp: When the measurement was taken
        created_at: When this record was created
    """
    
    id: UUID = field(default_factory=uuid4)
    station_id: UUID = field(default_factory=uuid4)
    pollutant_type: PollutantType = PollutantType.PM25
    value: float = 0.0
    unit: str = "µg/m³"
    quality_flag: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate reading value."""
        if self.value < 0:
            raise ValueError(f"Pollutant reading cannot be negative: {self.value}")
    
    @classmethod
    def create(
        cls,
        station_id: UUID,
        pollutant_type: str | PollutantType,
        value: float,
        timestamp: Optional[datetime] = None,
        quality_flag: Optional[str] = None,
    ) -> "PollutantReading":
        """Factory method to create a pollutant reading.
        
        Args:
            station_id: ID of the station
            pollutant_type: Type of pollutant
            value: Measured value
            timestamp: Measurement timestamp (defaults to now)
            quality_flag: Optional quality indicator
            
        Returns:
            New PollutantReading instance
        """
        if isinstance(pollutant_type, str):
            pollutant_type = PollutantType.from_string(pollutant_type)
        
        unit = pollutant_type.unit if isinstance(pollutant_type, PollutantType) else "µg/m³"
        
        return cls(
            id=uuid4(),
            station_id=station_id,
            pollutant_type=pollutant_type,
            value=value,
            unit=unit,
            quality_flag=quality_flag,
            timestamp=timestamp or datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
    
    def is_valid(self, min_value: float = 0.0, max_value: Optional[float] = None) -> bool:
        """Check if reading is within valid range.
        
        Args:
            min_value: Minimum acceptable value
            max_value: Maximum acceptable value (None for no upper limit)
            
        Returns:
            True if reading is valid
        """
        if self.value < min_value:
            return False
        if max_value is not None and self.value > max_value:
            return False
        return True
    
    @property
    def is_suspect(self) -> bool:
        """Return True if reading has been flagged as suspect."""
        return self.quality_flag in ("SUSPECT", "BAD")


@dataclass
class StationReadingBatch:
    """Aggregate of multiple pollutant readings from a single station at one time.
    
    This represents a complete air quality measurement set from a station,
    containing multiple pollutants measured at the same timestamp.
    
    Attributes:
        id: Unique identifier for this batch
        station_id: Reference to the station
        readings: Dictionary of pollutant readings
        timestamp: When measurements were taken
        source: Data source (API, WEBHOOK, MANUAL, FAKE)
        metadata: Additional metadata
    """
    
    id: UUID = field(default_factory=uuid4)
    station_id: UUID = field(default_factory=uuid4)
    readings: Dict[PollutantType, PollutantReading] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "API"
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def add_reading(self, reading: PollutantReading) -> None:
        """Add a pollutant reading to this batch.
        
        Args:
            reading: PollutantReading to add
        """
        self.readings[reading.pollutant_type] = reading
    
    def get_value(self, pollutant_type: str | PollutantType) -> Optional[float]:
        """Get the value for a specific pollutant.
        
        Args:
            pollutant_type: Type of pollutant to retrieve
            
        Returns:
            Pollutant value or None if not present
        """
        if isinstance(pollutant_type, str):
            pollutant_type = PollutantType.from_string(pollutant_type)
        
        reading = self.readings.get(pollutant_type)
        return reading.value if reading else None
    
    def get_all_values(self) -> Dict[str, float]:
        """Get all pollutant values as a dictionary.
        
        Returns:
            Dictionary mapping pollutant names to values
        """
        return {
            pt.value: reading.value
            for pt, reading in self.readings.items()
        }
    
    @property
    def has_pm25(self) -> bool:
        """Return True if batch contains PM2.5 reading."""
        return PollutantType.PM25 in self.readings
    
    @property
    def has_pm10(self) -> bool:
        """Return True if batch contains PM10 reading."""
        return PollutantType.PM10 in self.readings
    
    @property
    def reading_count(self) -> int:
        """Return number of readings in this batch."""
        return len(self.readings)
