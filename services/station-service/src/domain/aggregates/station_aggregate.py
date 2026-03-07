"""Station aggregate - wrapper for Station entity with additional aggregate logic."""
from __future__ import annotations

from typing import List
from ..entities.station import Station
from ..entities.pollutant_reading import PollutantReading, StationReadingBatch
from ..events.station_events import StationReadingsCreated


class StationAggregate:
    """Aggregate root for Station and its associated readings.
    
    This aggregate manages the station entity and coordinates
    the creation of reading entities, ensuring consistency.
    
    The aggregate ensures that:
    1. Readings can only be added to active stations
    2. Reading batches are validated before acceptance
    3. Domain events are properly emitted
    """
    
    def __init__(self, station: Station):
        """Initialize aggregate with a station.
        
        Args:
            station: Station entity
        """
        self.station = station
        self._pending_readings: List[StationReadingBatch] = []
    
    @classmethod
    def create(
        cls,
        name: str,
        station_code: str,
        station_type: str,
        latitude: float,
        longitude: float,
        altitude: float = None,
    ) -> "StationAggregate":
        """Factory method to create a new station aggregate.
        
        Args:
            name: Station name
            station_code: External station code
            station_type: Station type
            latitude: GPS latitude
            longitude: GPS longitude
            altitude: Optional altitude
            
        Returns:
            New StationAggregate instance
        """
        station = Station.create(
            name=name,
            station_code=station_code,
            station_type=station_type,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
        )
        return cls(station)
    
    def record_readings(
        self,
        readings: dict,
        timestamp: str = None,
        source: str = "API",
    ) -> StationReadingBatch:
        """Record a batch of readings from the station.
        
        Args:
            readings: Dictionary of pollutant_name -> value
            timestamp: Optional timestamp string (ISO format)
            source: Data source (API, WEBHOOK, MANUAL, FAKE)
            
        Returns:
            Created reading batch
            
        Raises:
            ValueError: If station is not active or readings are invalid
        """
        from datetime import datetime, timezone
        
        if not self.station.is_active:
            raise ValueError("Cannot record readings for inactive station")
        
        # Parse timestamp
        if timestamp:
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            ts = datetime.now(timezone.utc)
        
        # Create reading batch
        batch = StationReadingBatch(
            station_id=self.station.id,
            timestamp=ts,
            source=source,
        )
        
        # Add individual readings
        for pollutant_name, value in readings.items():
            if value is not None and value >= 0:
                reading = PollutantReading.create(
                    station_id=self.station.id,
                    pollutant_type=pollutant_name,
                    value=value,
                    timestamp=ts,
                )
                batch.add_reading(reading)
        
        self._pending_readings.append(batch)
        
        # Record that data was received
        self.station.record_data_received()
        
        # Emit event with reading data
        self.station._events.append(
            StationReadingsCreated(
                station_id=self.station.id,
                readings=readings,
                timestamp=ts,
                source=source,
            )
        )
        
        return batch
    
    def get_pending_readings(self) -> List[StationReadingBatch]:
        """Get pending reading batches that haven't been persisted.
        
        Returns:
            List of pending reading batches
        """
        readings = self._pending_readings.copy()
        self._pending_readings.clear()
        return readings
    
    def collect_events(self) -> List:
        """Collect and clear domain events from the station.
        
        Returns:
            List of domain events
        """
        return self.station.collect_events()
