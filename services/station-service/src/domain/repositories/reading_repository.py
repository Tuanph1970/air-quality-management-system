"""Reading repository interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..entities.pollutant_reading import PollutantReading, StationReadingBatch


class ReadingRepository(ABC):
    """Repository interface for pollutant readings.
    
    This is a port (interface) defined in the domain layer.
    Implementations live in the infrastructure layer.
    """
    
    @abstractmethod
    async def save_reading(self, reading: PollutantReading) -> PollutantReading:
        """Save a single pollutant reading.
        
        Args:
            reading: Reading to save
            
        Returns:
            Saved reading
        """
        pass
    
    @abstractmethod
    async def save_batch(self, batch: StationReadingBatch) -> StationReadingBatch:
        """Save a batch of readings from a station.
        
        Args:
            batch: Batch of readings to save
            
        Returns:
            Saved batch
        """
        pass
    
    @abstractmethod
    async def get_by_station_id(
        self,
        station_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        pollutant_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PollutantReading]:
        """Get readings for a station.
        
        Args:
            station_id: Station UUID
            start_time: Filter readings after this time
            end_time: Filter readings before this time
            pollutant_type: Filter by pollutant type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of readings
        """
        pass
    
    @abstractmethod
    async def get_latest_by_station(
        self,
        station_id: UUID,
        pollutant_types: Optional[List[str]] = None,
    ) -> Dict[str, PollutantReading]:
        """Get the latest reading for each pollutant type from a station.
        
        Args:
            station_id: Station UUID
            pollutant_types: Optional list of pollutant types to retrieve
            
        Returns:
            Dictionary mapping pollutant type to latest reading
        """
        pass
    
    @abstractmethod
    async def get_readings_in_timerange(
        self,
        station_ids: List[UUID],
        start_time: datetime,
        end_time: datetime,
        pollutant_types: Optional[List[str]] = None,
    ) -> List[StationReadingBatch]:
        """Get readings grouped by timestamp for multiple stations.
        
        Args:
            station_ids: List of station UUIDs
            start_time: Start of time range
            end_time: End of time range
            pollutant_types: Optional filter by pollutant types
            
        Returns:
            List of reading batches
        """
        pass
    
    @abstractmethod
    async def delete_old_readings(self, older_than: datetime) -> int:
        """Delete readings older than specified timestamp.
        
        Used for data retention policy enforcement.
        
        Args:
            older_than: Delete readings before this timestamp
            
        Returns:
            Number of readings deleted
        """
        pass
