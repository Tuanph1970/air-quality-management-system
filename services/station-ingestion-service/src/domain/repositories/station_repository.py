"""Station repository interface."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.domain.entities.station import AirQualityReading, Station


class StationRepository(ABC):
    """Repository interface for station operations."""

    @abstractmethod
    async def get_all_stations(self) -> List[Station]:
        """Get all stations.

        Returns:
            List of all stations
        """
        pass

    @abstractmethod
    async def get_station_by_code(self, station_code: str) -> Optional[Station]:
        """Get station by station code.

        Args:
            station_code: Station code

        Returns:
            Station or None if not found
        """
        pass

    @abstractmethod
    async def save_station(self, station: Station) -> Station:
        """Save or update a station.

        Args:
            station: Station to save

        Returns:
            Saved station
        """
        pass

    @abstractmethod
    async def save_stations(self, stations: List[Station]) -> List[Station]:
        """Save or update multiple stations.

        Args:
            stations: List of stations to save

        Returns:
            List of saved stations
        """
        pass

    @abstractmethod
    async def get_readings_by_station(
        self,
        station_code: str,
        from_time: datetime,
        to_time: datetime,
    ) -> List[AirQualityReading]:
        """Get readings for a station within time range.

        Args:
            station_code: Station code
            from_time: Start time
            to_time: End time

        Returns:
            List of readings
        """
        pass

    @abstractmethod
    async def get_readings_all_stations(
        self,
        from_time: datetime,
        to_time: datetime,
    ) -> List[AirQualityReading]:
        """Get readings for all stations within time range.

        Args:
            from_time: Start time
            to_time: End time

        Returns:
            List of readings
        """
        pass

    @abstractmethod
    async def save_readings(self, readings: List[AirQualityReading]) -> List[AirQualityReading]:
        """Save multiple readings.

        Args:
            readings: List of readings to save

        Returns:
            List of saved readings
        """
        pass
