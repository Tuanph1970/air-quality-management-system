"""PurpleAir cloud polling service."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.config import settings, PurpleAirSensorConfig
from ..core.publisher import get_publisher
from ..core.events import PurpleAirDataIngested
from ..external.purpleair_client import PurpleAirAPIClient
from .data_storage import RawDataStorage

logger = logging.getLogger(__name__)


class PollingService:
    """Poll PurpleAir cloud API for sensor data.
    
    Runs as a background task, fetching data from configured sensors
    at regular intervals and publishing events for processing.
    """
    
    def __init__(self):
        """Initialize polling service."""
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._client: Optional[PurpleAirAPIClient] = None
        self._storage: Optional[RawDataStorage] = None
        self._sensors: List[PurpleAirSensorConfig] = list(settings.PURPLEAIR_SENSORS)
        self._polling_interval_hours: int = settings.PURPLEAIR_POLLING_INTERVAL_HOURS
    
    def add_sensor(self, sensor: PurpleAirSensorConfig) -> None:
        """Add a sensor to the polling list.
        
        Args:
            sensor: Sensor configuration to add
        """
        # Check if sensor already exists
        for existing in self._sensors:
            if existing.sensor_id == sensor.sensor_id:
                logger.warning(f"Sensor {sensor.sensor_id} already in polling list")
                return
        
        self._sensors.append(sensor)
        logger.info(f"Added sensor {sensor.sensor_id} to polling list")
    
    def remove_sensor(self, sensor_id: int) -> bool:
        """Remove a sensor from the polling list.
        
        Args:
            sensor_id: Sensor ID to remove
            
        Returns:
            True if sensor was removed, False if not found
        """
        for i, sensor in enumerate(self._sensors):
            if sensor.sensor_id == sensor_id:
                self._sensors.pop(i)
                logger.info(f"Removed sensor {sensor_id} from polling list")
                return True
        
        logger.warning(f"Sensor {sensor_id} not found in polling list")
        return False
    
    def list_sensors(self) -> List[PurpleAirSensorConfig]:
        """Get list of configured sensors.
        
        Returns:
            List of sensor configurations
        """
        return list(self._sensors)
    
    async def _fetch_sensor_data(
        self,
        sensor: PurpleAirSensorConfig,
    ) -> Optional[Dict[str, Any]]:
        """Fetch data for a single sensor from PurpleAir API.
        
        Args:
            sensor: Sensor configuration
            
        Returns:
            Sensor data dictionary or None if failed
        """
        if self._client is None:
            self._client = PurpleAirAPIClient(sensor.api_key or settings.PURPLEAIR_API_KEY)
        
        try:
            # Fetch sensor data from PurpleAir API
            data = await self._client.get_sensor(sensor.sensor_id)
            
            if data is None:
                logger.warning(f"Failed to fetch data for sensor {sensor.sensor_id}")
                return None
            
            # Save raw data
            if self._storage is None:
                self._storage = RawDataStorage(settings.PURPLEAIR_RAW_DATA_DIR)
            
            self._storage.save_reading(sensor.sensor_id, data)
            logger.debug(f"Saved raw data for sensor {sensor.sensor_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching sensor {sensor.sensor_id}: {e}")
            return None
    
    def _parse_sensor_data(
        self,
        sensor: PurpleAirSensorConfig,
        raw_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Parse raw PurpleAir API response to standard format.
        
        Args:
            sensor: Sensor configuration
            raw_data: Raw API response
            
        Returns:
            Parsed readings dictionary or None if parsing failed
        """
        try:
            # PurpleAir API v1 response structure
            # The actual data is in 'results' or directly in the response
            results = raw_data.get("results", {})
            if isinstance(results, list) and results:
                results = results[0]
            
            # Get channel data (PurpleAir devices have dual channels)
            channel_data = results.get("current_reading", results)
            
            # Extract PM values (use primary channel or average)
            pm2_5 = channel_data.get("pm2_5") or channel_data.get("PM2_5") or channel_data.get("pm25_a") or channel_data.get("pm2_5_a")
            pm10_0 = channel_data.get("pm10_0") or channel_data.get("PM10") or channel_data.get("pm100_a") or channel_data.get("pm10_0_a")
            pm1_0 = channel_data.get("pm1_0") or channel_data.get("PM1") or channel_data.get("pm1_a") or channel_data.get("pm1_0_a")
            
            # Extract environmental data
            temperature = channel_data.get("temperature") or channel_data.get("temp_f")
            if temperature and "temp_f" in str(channel_data.get("temperature", "")):
                # Convert Fahrenheit to Celsius if needed
                try:
                    temp_f = float(str(temperature).replace("°F", "").strip())
                    temperature = (temp_f - 32) * 5 / 9
                except (ValueError, TypeError):
                    temperature = None
            
            humidity = channel_data.get("humidity") or channel_data.get("humidity_a") or channel_data.get("relative_humidity")
            pressure = channel_data.get("pressure") or channel_data.get("pressure_a") or channel_data.get("baro_pressure")
            
            # Extract gas data (if available from BME688)
            ozone = channel_data.get("ozone") or channel_data.get("O3")
            no2 = channel_data.get("no2") or channel_data.get("NO2")
            co = channel_data.get("co") or channel_data.get("CO")
            
            # Build readings dictionary
            readings = {}
            
            if pm2_5 is not None:
                readings["PM25"] = float(pm2_5)
            if pm10_0 is not None:
                readings["PM10"] = float(pm10_0)
            if pm1_0 is not None:
                readings["PM1"] = float(pm1_0)
            if temperature is not None:
                readings["temperature"] = float(temperature)
            if humidity is not None:
                readings["humidity"] = float(humidity)
            if pressure is not None:
                readings["pressure"] = float(pressure)
            if ozone is not None:
                readings["O3"] = float(ozone)
            if no2 is not None:
                readings["NO2"] = float(no2)
            if co is not None:
                readings["CO"] = float(co)
            
            if not readings:
                logger.warning(f"No valid readings found for sensor {sensor.sensor_id}")
                return None
            
            return readings
            
        except Exception as e:
            logger.error(f"Error parsing sensor data for {sensor.sensor_id}: {e}")
            return None
    
    async def _process_sensor(
        self,
        sensor: PurpleAirSensorConfig,
    ) -> bool:
        """Fetch and process data for a single sensor.
        
        Args:
            sensor: Sensor configuration
            
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Fetch raw data
            raw_data = await self._fetch_sensor_data(sensor)
            if raw_data is None:
                return False
            
            # Parse to standard format
            readings = self._parse_sensor_data(sensor, raw_data)
            if readings is None:
                return False
            
            # Get coordinates from sensor config or API response
            latitude = sensor.latitude
            longitude = sensor.longitude
            
            if latitude == 0.0 and longitude == 0.0:
                # Try to get from API response
                results = raw_data.get("results", {})
                if isinstance(results, list) and results:
                    results = results[0]
                latitude = float(results.get("latitude", 0.0))
                longitude = float(results.get("longitude", 0.0))
            
            # Generate internal sensor ID
            internal_sensor_id = f"purpleair-{sensor.sensor_id}"
            
            # Create and publish event
            event = PurpleAirDataIngested(
                event_id=None,  # Auto-generated
                sensor_id=__import__("uuid").UUID(int=hash(internal_sensor_id) & (2**128 - 1)),
                purpleair_sensor_id=sensor.sensor_id,
                readings=readings,
                timestamp=datetime.utcnow(),
                latitude=latitude,
                longitude=longitude,
            )
            
            publisher = get_publisher()
            await publisher.publish(event)
            
            logger.info(
                f"Processed sensor {sensor.sensor_id} ({sensor.name or 'unnamed'}): "
                f"PM2.5={readings.get('PM25', 'N/A')}, PM10={readings.get('PM10', 'N/A')}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing sensor {sensor.sensor_id}: {e}", exc_info=True)
            return False
    
    async def _poll_all_sensors(self) -> None:
        """Poll all configured sensors."""
        if not self._sensors:
            logger.debug("No sensors configured for polling")
            return
        
        logger.info(f"Polling {len(self._sensors)} sensors...")
        
        success_count = 0
        for sensor in self._sensors:
            if await self._process_sensor(sensor):
                success_count += 1
        
        logger.info(f"Polling complete: {success_count}/{len(self._sensors)} sensors succeeded")
    
    async def _run_loop(self) -> None:
        """Main polling loop."""
        logger.info(
            f"Starting polling service (interval={self._polling_interval_hours}h, "
            f"sensors={len(self._sensors)})"
        )
        
        while self._running:
            try:
                await self._poll_all_sensors()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
            
            # Wait for next polling interval
            if self._running:
                wait_seconds = self._polling_interval_hours * 3600
                logger.debug(f"Next poll in {wait_seconds} seconds")
                await asyncio.sleep(wait_seconds)
    
    async def start(self) -> None:
        """Start the polling service."""
        if self._running:
            logger.warning("Polling service already running")
            return
        
        if not self._sensors:
            logger.warning("No sensors configured, polling service will not start")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Polling service started")
    
    async def stop(self) -> None:
        """Stop the polling service."""
        if not self._running:
            return
        
        logger.info("Stopping polling service...")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Close API client
        if self._client:
            await self._client.close()
        
        logger.info("Polling service stopped")
    
    async def poll_now(self) -> Dict[str, bool]:
        """Trigger immediate polling of all sensors.
        
        Returns:
            Dictionary of sensor_id -> success status
        """
        results = {}
        for sensor in self._sensors:
            success = await self._process_sensor(sensor)
            results[sensor.sensor_id] = success
        
        return results


# Global instance
_polling_service: Optional[PollingService] = None


def get_polling_service() -> PollingService:
    """Get the polling service instance."""
    global _polling_service
    if _polling_service is None:
        _polling_service = PollingService()
    return _polling_service
