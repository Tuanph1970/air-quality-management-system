"""Event consumers for Air Quality Service.

Listens to sensor events and updates cache accordingly.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine, Dict

from .redis_cache import RedisCache

logger = logging.getLogger(__name__)

# Type alias for event handler signature.
EventHandler = Callable[
    [Dict[str, Any], Any],
    Coroutine[Any, Any, None],
]

# Module-level cache reference.
_cache: RedisCache | None = None


def set_cache_for_handler(cache: RedisCache) -> None:
    """Inject the shared cache instance."""
    global _cache
    _cache = cache


class AirQualityEventHandler:
    """Handles inbound events for air quality updates.

    Events consumed:
        ``sensor.reading.created`` → Update AQI cache for location
        ``alert.violation.detected`` → Log for forecasting
        ``alert.violation.resolved`` → Log for forecasting
    """

    # ------------------------------------------------------------------
    # sensor.reading.created
    # ------------------------------------------------------------------
    @staticmethod
    async def handle_sensor_reading(
        event_data: Dict[str, Any],
        message: Any,
    ) -> None:
        """Process an incoming sensor reading and update cache.

        Flow:
        1. Parse the sensor reading event
        2. Calculate AQI from pollutant concentrations
        3. Update cache for the location
        4. Ack the message
        """
        from ...domain.services.aqi_calculator import AQICalculator

        sensor_id = event_data.get("sensor_id")
        factory_id = event_data.get("factory_id")
        latitude = event_data.get("latitude", 0.0)
        longitude = event_data.get("longitude", 0.0)

        if not sensor_id:
            logger.warning("SensorReadingCreated missing sensor_id — acking")
            await message.ack()
            return

        # Extract pollutant concentrations
        pollutants = {}
        for key in ("pm25", "pm10", "co", "no2", "so2", "o3"):
            value = event_data.get(key)
            if value is not None:
                try:
                    pollutants[key] = float(value)
                except (ValueError, TypeError):
                    pass

        if not pollutants:
            logger.debug("No valid pollutants in reading — acking")
            await message.ack()
            return

        # Calculate AQI
        calculator = AQICalculator()
        aqi_result = calculator.calculate_composite_aqi(pollutants)

        # Update cache
        if _cache:
            aqi_data = {
                "location_lat": latitude,
                "location_lng": longitude,
                "aqi_value": aqi_result.aqi_value,
                "level": aqi_result.level.value,
                "category": aqi_result.category,
                "color": aqi_result.color,
                "dominant_pollutant": aqi_result.dominant_pollutant,
                "pollutants": {
                    "concentrations": pollutants,
                    "individual_aqis": calculator.get_all_pollutant_aqis(pollutants),
                },
                "health_message": aqi_result.health_message,
                "caution_message": aqi_result.caution_message,
                "sensor_id": sensor_id,
                "factory_id": factory_id,
            }

            await _cache.set_aqi(latitude, longitude, 10.0, aqi_data)
            logger.info(
                "Updated AQI cache for sensor %s: AQI=%d (%s)",
                sensor_id,
                aqi_result.aqi_value,
                aqi_result.level.value,
            )

        await message.ack()

    # ------------------------------------------------------------------
    # alert.violation.detected / resolved (for forecasting)
    # ------------------------------------------------------------------
    @staticmethod
    async def handle_violation_event(
        event_data: Dict[str, Any],
        message: Any,
    ) -> None:
        """Log violation events for forecasting analysis."""
        violation_id = event_data.get("violation_id")
        event_type = event_data.get("event_type", "unknown")

        logger.info(
            "Received violation event: %s (id=%s)",
            event_type,
            violation_id,
        )

        # Could store in time-series for forecast model training
        await message.ack()

    # ------------------------------------------------------------------
    # Handler registry
    # ------------------------------------------------------------------
    def get_handlers(self) -> Dict[str, EventHandler]:
        """Return mapping of queue name → handler."""
        from shared.messaging.config import (
            AQ_SENSOR_READINGS_QUEUE,
            AQ_ALERT_EVENTS_QUEUE,
        )

        return {
            AQ_SENSOR_READINGS_QUEUE: self.handle_sensor_reading,
            AQ_ALERT_EVENTS_QUEUE: self.handle_violation_event,
        }
