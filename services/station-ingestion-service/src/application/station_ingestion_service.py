"""Application services for station ingestion."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities.station import AirQualityReading, Station
from src.domain.repositories.station_repository import StationRepository
from src.infrastructure.external.station_api_client import StationAPIClient
from src.core.config import config

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
            Tuple of (total stations saved, new stations count)
        """
        logger.info("Starting station synchronization...")

        # Use fake data mode for development/testing
        if config.USE_FAKE_DATA:
            logger.info("USE_FAKE_DATA is enabled. Using fake station data...")
            from src.infrastructure.external.fake_data_seeder import create_fake_stations
            stations = create_fake_stations()
            # Count how many are truly new
            new_count = 0
            for station in stations:
                existing = await self.repository.get_station_by_code(station.station_code)
                if not existing:
                    new_count += 1
            saved_stations = await self.repository.save_stations(stations)
            logger.info(f"Saved {len(saved_stations)} fake stations ({new_count} new)")
            return len(saved_stations), new_count

        # Fetch all stations from external API
        response = await self.api_client.get_automation_stations(page=0, size=1000)

        if not response:
            # Stations endpoint failed — fall back to extracting stations from AQI data
            logger.warning("Stations endpoint unavailable — extracting stations from recent AQI data")
            return await self._sync_stations_from_aqi()

        content = response.get("content", [])
        total_elements = response.get("totalElements", len(content))

        logger.info(f"Fetched {len(content)} stations from API (total reported: {total_elements})")

        if not content:
            return await self._sync_stations_from_aqi()

        # Count new vs existing before saving
        new_count = 0
        for item in content:
            code = item.get("stationCode", "")
            if code:
                existing = await self.repository.get_station_by_code(code)
                if not existing:
                    new_count += 1

        # Convert to entities and save
        stations = [Station.from_api_data(data) for data in content if data.get("stationCode")]
        saved_stations = await self.repository.save_stations(stations)

        logger.info(f"Saved {len(saved_stations)} stations ({new_count} new)")
        return len(saved_stations), new_count

    async def _sync_stations_from_aqi(self) -> Tuple[int, int]:
        """Extract and save station metadata from recent AQI data as fallback.

        Fetches the last hour of AQI data and extracts unique stationCode/stationName
        pairs to populate the stations table.

        Returns:
            Tuple of (total stations saved, new stations count)
        """
        from datetime import timedelta
        to_time = datetime.utcnow()
        from_time = to_time - timedelta(hours=1)

        logger.info("Fetching AQI data to extract station list...")
        response = await self.api_client.get_aqi_hours(from_time=from_time, to_time=to_time, size=500)
        if not response:
            logger.error("Failed to fetch AQI data for station extraction")
            return 0, 0

        content = response.get("content", [])
        if not content:
            logger.warning("No AQI content returned for station extraction")
            return 0, 0

        seen: dict = {}
        for item in content:
            if not isinstance(item, dict):
                continue
            code = item.get("stationCode")
            name = item.get("stationName", code or "")
            if code and code not in seen:
                seen[code] = name

        logger.info(f"Discovered {len(seen)} stations from AQI data")

        new_count = 0
        stations_to_save = []
        import uuid as _uuid
        for code, name in seen.items():
            existing = await self.repository.get_station_by_code(code)
            if not existing:
                new_count += 1
            stations_to_save.append(Station(
                id=str(_uuid.uuid4()),
                station_code=code,
                station_name=name,
                is_active=True,
            ))

        saved = await self.repository.save_stations(stations_to_save)
        logger.info(f"Saved {len(saved)} stations from AQI fallback ({new_count} new)")
        return len(saved), new_count

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

        # Step 1: Ensure stations exist in database
        valid_stations = await self.repository.get_all_stations()
        valid_codes = {s.station_code for s in valid_stations}

        if not valid_codes:
            logger.info("No stations in database. Fetching stations from external API first...")
            stations_synced, _ = await self.sync_stations()
            if stations_synced == 0:
                logger.error("Failed to fetch stations. Cannot sync AQI data without stations.")
                return 0
            # Reload valid codes after syncing stations
            valid_stations = await self.repository.get_all_stations()
            valid_codes = {s.station_code for s in valid_stations}
            logger.info(f"Loaded {len(valid_codes)} stations for AQI sync")

        # Step 2: Use fake data or fetch from external API
        readings: List[AirQualityReading] = []

        if config.USE_FAKE_DATA:
            # Generate fake readings for development/testing
            logger.info("USE_FAKE_DATA is enabled. Generating fake AQI readings...")
            from src.infrastructure.external.fake_data_seeder import create_fake_readings
            hours = int((to_time - from_time).total_seconds() / 3600)
            readings = create_fake_readings(list(valid_codes), hours=hours)
            logger.info(f"Generated {len(readings)} fake readings")
        else:
            # Fetch AQI data from external API
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

            # Step 3: Parse readings from response.
            # API response format — content is a list of objects:
            # [
            #   {
            #     "stationCode": "GLHN_KHINVC",
            #     "stationName": "...",
            #     "data": [
            #       { "id": "...", "getTime": "2026-03-14T02:00:00",
            #         "data": { "aqi": 103.95, "PM205": 103.95, "PM10": 70.89, "NO2": 14.1, ... }
            #       }
            #     ]
            #   }
            # ]
            readings = []
            stations_from_aqi: List[Station] = []

            for item in content:
                if not isinstance(item, dict):
                    continue

                station_code = item.get("stationCode")
                station_name = item.get("stationName", "")
                station_readings = item.get("data", [])

                if not station_code or not isinstance(station_code, str):
                    logger.warning(f"Skipping item without valid stationCode")
                    continue

                # Collect station info from AQI response to auto-register unknown stations
                if station_code not in valid_codes:
                    import uuid as _uuid
                    stations_from_aqi.append(Station(
                        id=str(_uuid.uuid4()),
                        station_code=station_code,
                        station_name=station_name,
                        is_active=True,
                    ))

                if not isinstance(station_readings, list):
                    logger.warning(f"Skipping station {station_code}: expected list")
                    continue

                for reading_data in station_readings:
                    if not isinstance(reading_data, dict):
                        continue
                    try:
                        reading = AirQualityReading.from_api_data(station_code, reading_data)
                        readings.append(reading)
                    except Exception as e:
                        logger.warning(f"Failed to parse reading for station {station_code}: {e}")

            # Auto-register any stations found in AQI data but not yet in DB
            if stations_from_aqi:
                logger.info(f"Auto-registering {len(stations_from_aqi)} stations discovered from AQI response")
                await self.repository.save_stations(stations_from_aqi)

            if not readings:
                logger.warning("No valid readings parsed — check API response format")
                logger.debug(f"Sample content item: {content[0] if content else 'empty'}")
                return 0

        # Step 4: Save readings
        saved = await self.repository.save_readings(readings)
        logger.info(f"Saved {len(saved)} readings")

        return len(saved)

    async def get_stations_with_latest_reading(
        self,
    ) -> List[Dict[str, Any]]:
        """Get all stations with their latest reading.

        If no stations exist in the database, automatically fetches them
        from the external API first.

        Returns:
            List of station data with latest reading
        """
        stations = await self.repository.get_all_stations()

        if not stations:
            logger.info("No stations in database — fetching from external API...")
            total, new = await self.sync_stations()
            if total > 0:
                logger.info(f"Auto-synced {total} stations ({new} new) on first load")
                stations = await self.repository.get_all_stations()
            else:
                logger.warning("Could not fetch stations from external API")

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
