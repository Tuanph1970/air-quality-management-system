"""Station repository interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.station import Station


class StationRepository(ABC):
    """Repository interface for Station aggregate.
    
    This is a port (interface) defined in the domain layer.
    Implementations live in the infrastructure layer.
    """
    
    @abstractmethod
    async def get_by_id(self, station_id: UUID) -> Optional[Station]:
        """Get station by ID.
        
        Args:
            station_id: Station UUID
            
        Returns:
            Station or None if not found
        """
        pass
    
    @abstractmethod
    async def get_by_station_code(self, station_code: str) -> Optional[Station]:
        """Get station by external station code.
        
        Args:
            station_code: External identifier (e.g., EPA station ID)
            
        Returns:
            Station or None if not found
        """
        pass
    
    @abstractmethod
    async def list_all(
        self,
        station_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Station]:
        """List stations with optional filters.
        
        Args:
            station_type: Filter by station type
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of stations
        """
        pass
    
    @abstractmethod
    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 10,
    ) -> List[Station]:
        """Find stations near a location.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            
        Returns:
            List of stations within radius
        """
        pass
    
    @abstractmethod
    async def save(self, station: Station) -> Station:
        """Save a station.
        
        Args:
            station: Station to save
            
        Returns:
            Saved station
        """
        pass
    
    @abstractmethod
    async def delete(self, station_id: UUID) -> bool:
        """Delete a station.
        
        Args:
            station_id: Station UUID
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count(self, station_type: Optional[str] = None) -> int:
        """Count stations.
        
        Args:
            station_type: Optional filter by type
            
        Returns:
            Number of stations
        """
        pass
