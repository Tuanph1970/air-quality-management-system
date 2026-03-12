"""Application services for station ingestion."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities.station import AirQualityReading, Station
from src.domain.repositories.station_repository import StationRepository
from src.infrastructure.external.station_api_client import StationAPIClient

logger = logging.getLogger(__name__)


class StationIngestionService:
    """Service for ingesting station data from external API.

    Responsibilities:
    - Fetch stations from external API
    - Fetch AQI readings from external API
    - Save data to local database
    """

    def __init__(
        self,
        station_repository: StationRepository,
        api_client: StationAPIClient,
    ):
        """Initialize service.

        Args:
            station_repository: Repository for station operations
            api_client: Client for external API
        """
        self.repository = station_repository
        self.api_client = api_client

    async def sync_stations(self) -> Tuple[int, int]:
        """Synchronize stations from external API.

        Returns:
            Tuple of (total stations, new stations count)
        """
        logger.info("Starting station synchronization...")

        # Fetch all stations from external API
        response = await self.api_client.get_automation_stations(page=0, size=1000)

        if not response:
            logger.error("Failed to fetch stations from external API")
            return 0, 0

        content = response.get("content", [])
        total_elements = response.get("totalElements", len(content))

        logger.info(f"Fetched {len(content)} stations (total: {total_elements})")

        # Convert to entities and save
        stations = [Station.from_api_data(data) for data in content]
        saved_stations = await self.repository.save_stations(stations)

        logger.info(f"Saved {len(saved_stations)} stations")

        return len(saved_stations), 0

    async def sync_aqi_data(
        self,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
    ) -> int:
        """Synchronize AQI data from external API.

        Args:
            from_time: Start time (defaults to 24 hours ago)
            to_time: End time (defaults to now)

        Returns:
            Number of readings saved
        """
        if from_time is None:
            from_time = datetime.utcnow() - timedelta(hours=24)
        if to_time is None:
            to_time = datetime.utcnow()

        logger.info(f"Syncing AQI data from {from_time} to {to_time}")

        # Fetch AQI data
        response = await self.api_client.get_aqi_hours(
            from_time=from_time,
            to_time=to_time,
            page=0,
            size=100,
        )

        if not response:
            logger.error("Failed to fetch AQI data from external API")
            return 0

        content = response.get("content", [])
        if not content:
            logger.info("No AQI data found")
            return 0

        # Parse readings from response
        # Response format: content is a list with one item that maps stationCode -> readings
        readings: List[AirQualityReading] = []

        for item in content:
            if isinstance(item, dict):
                for station_code, station_readings in item.items():
                    if isinstance(station_readings, list):
                        for reading_data in station_readings:
                            try:
                                reading = AirQualityReading.from_api_data(
                                    station_code, reading_data
                                )
                                readings.append(reading)
                            except Exception as e:
                                logger.warning(f"Failed to parse reading: {e}")

        if not readings:
            logger.info("No valid readings to save")
            return 0

        # Save readings
        saved = await self.repository.save_readings(readings)
        logger.info(f"Saved {len(saved)} readings")

        return len(saved)

    async def get_stations_with_latest_reading(
        self,
    ) -> List[Dict[str, Any]]:
        """Get all stations with their latest reading.

        Returns:
            List of station data with latest reading
        """
        stations = await self.repository.get_all_stations()
        result = []

        for station in stations:
            # Get latest reading (last 1 hour)
            from_time = datetime.utcnow() - timedelta(hours=1)
            to_time = datetime.utcnow()

            readings = await self.repository.get_readings_by_station(
                station.station_code, from_time, to_time
            )

            latest = readings[-1] if readings else None

            result.append(
                {
                    "id": station.id,
                    "station_code": station.station_code,
                    "station_name": station.station_name,
                    "address": station.address,
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                    "station_type": station.station_type,
                    "is_active": station.is_active,
                    "latest_reading": self._reading_to_dict(latest) if latest else None,
                }
            )

        return result

    def _reading_to_dict(self, reading: AirQualityReading) -> Dict[str, Any]:
        """Convert reading to dictionary."""
        return {
            "id": reading.id,
            "station_code": reading.station_code,
            "reading_time": reading.reading_time.isoformat(),
            "aqi": reading.aqi,
            "pm25": reading.pm25,
            "pm10": reading.pm10,
            "co": reading.co,
            "so2": reading.so2,
            "no2": reading.no2,
            "o3": reading.o3,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
        }
