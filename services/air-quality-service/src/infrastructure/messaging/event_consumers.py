"""Event consumers for Air Quality Service.

Listens to sensor events and updates cache accordingly.
Also provides specialized consumers for satellite data fusion
and cross-validation workflows.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import uuid4

import aio_pika

from ..cache.redis_cache import RedisCache

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
        ``sensor.reading.created`` -> Update AQI cache for location
        ``alert.violation.detected`` -> Log for forecasting
        ``alert.violation.resolved`` -> Log for forecasting
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
        """Return mapping of queue name -> handler."""
        from shared.messaging.config import (
            AQ_SENSOR_READINGS_QUEUE,
            AQ_ALERT_EVENTS_QUEUE,
        )

        return {
            AQ_SENSOR_READINGS_QUEUE: self.handle_sensor_reading,
            AQ_ALERT_EVENTS_QUEUE: self.handle_violation_event,
        }


# =====================================================================
# Satellite Data Consumer — listens for satellite.data.fetched events
# =====================================================================


class SatelliteDataConsumer:
    """Consumes satellite data events and triggers data fusion.

    Listens to ``satellite.data.fetched`` events from the Remote Sensing
    Service.  When new satellite data arrives:
    1. Fetch nearby sensor readings from the Sensor Service
    2. Run data fusion (sensor + satellite calibration)
    3. Cache the fused results
    4. Publish ``data.fusion.completed`` event

    Uses direct aio-pika connection management.
    """

    EXCHANGE_NAME = "satellite.events"
    QUEUE_NAME = "aq.satellite.data.queue"
    ROUTING_KEY = "satellite.data.fetched"
    FUSION_EXCHANGE = "fusion.events"

    def __init__(
        self,
        rabbitmq_url: str,
        sensor_client: Any,
        cache: RedisCache,
    ):
        self.rabbitmq_url = rabbitmq_url
        self.sensor_client = sensor_client
        self.cache = cache
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._consumer_tag: Optional[str] = None

    async def start(self) -> None:
        """Connect to RabbitMQ and begin consuming satellite events."""
        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        # Declare exchange and queue
        exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        queue = await self._channel.declare_queue(
            self.QUEUE_NAME,
            durable=True,
        )
        await queue.bind(exchange, routing_key=self.ROUTING_KEY)

        # Start consuming
        self._consumer_tag = await queue.consume(self._on_message)
        logger.info(
            "SatelliteDataConsumer started — listening on %s",
            self.QUEUE_NAME,
        )

    async def stop(self) -> None:
        """Gracefully stop consuming and close connection."""
        if self._channel:
            try:
                await self._channel.close()
            except Exception:
                pass
        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
        logger.info("SatelliteDataConsumer stopped")

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        """Handle an incoming satellite data event."""
        try:
            event_data = json.loads(message.body.decode())
            await self._process_satellite_data(event_data)
            await message.ack()
        except json.JSONDecodeError:
            logger.error("Invalid JSON in satellite event — rejecting")
            await message.reject(requeue=False)
        except Exception as e:
            logger.error("Error processing satellite event: %s", e)
            await message.nack(requeue=True)

    async def _process_satellite_data(
        self, event_data: Dict[str, Any]
    ) -> None:
        """Run data fusion with satellite and sensor data.

        Steps:
        1. Parse satellite grid cells from event
        2. Fetch nearby sensor readings from Sensor Service
        3. Run calibration + fusion via domain services
        4. Cache the fused result
        5. Publish DataFusionCompleted event
        """
        from ...domain.services.calibration_model import CalibrationModel
        from ...domain.services.data_fusion import DataFusionService

        source = event_data.get("source", "unknown")
        grid_cells = event_data.get("grid_cells", [])
        observation_time = event_data.get("observation_time")

        if not grid_cells:
            logger.debug("Satellite event has no grid_cells — skipping fusion")
            return

        logger.info(
            "Processing satellite data from %s (%d grid cells)",
            source,
            len(grid_cells),
        )

        # Get bounding box from grid cells
        lats = [c.get("lat", 0) for c in grid_cells]
        lons = [c.get("lon", 0) for c in grid_cells]
        center_lat = sum(lats) / len(lats) if lats else 0
        center_lon = sum(lons) / len(lons) if lons else 0

        # Fetch nearby sensor readings
        sensor_readings: List[Dict] = []
        try:
            readings = await self.sensor_client.get_recent_readings(
                latitude=center_lat,
                longitude=center_lon,
                radius_km=50.0,
                limit=100,
            )
            sensor_readings = [
                {
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "pm25": r.pm25,
                    "pm10": r.pm10,
                    "temperature": 25.0,  # Default if not in reading
                    "humidity": 50.0,  # Default if not in reading
                }
                for r in readings
            ]
        except Exception as e:
            logger.warning("Could not fetch sensor readings: %s", e)

        # Run data fusion
        timestamp = (
            datetime.fromisoformat(observation_time)
            if observation_time
            else datetime.utcnow()
        )

        calibration_model = CalibrationModel()
        fusion_service = DataFusionService(calibration_model)

        satellite_data = {"grid_cells": grid_cells}
        fused_points = fusion_service.fuse_data(
            sensor_readings=sensor_readings,
            satellite_data=satellite_data,
            timestamp=timestamp,
        )

        # Cache fused results
        if self.cache and fused_points:
            for point in fused_points:
                if point.fused_aqi is not None:
                    aqi_data = {
                        "location_lat": point.location.latitude,
                        "location_lng": point.location.longitude,
                        "aqi_value": point.fused_aqi,
                        "fused_pm25": point.fused_pm25,
                        "fused_pm10": point.fused_pm10,
                        "confidence": point.confidence,
                        "data_sources": point.data_sources,
                        "timestamp": timestamp.isoformat(),
                    }
                    await self.cache.set_aqi(
                        point.location.latitude,
                        point.location.longitude,
                        10.0,
                        aqi_data,
                    )

            logger.info(
                "Fused %d data points from %s satellite data",
                len(fused_points),
                source,
            )

        # Publish DataFusionCompleted event
        await self._publish_fusion_completed(
            source=source,
            fused_count=len(fused_points),
            sensor_count=len(sensor_readings),
            timestamp=timestamp,
        )

    async def _publish_fusion_completed(
        self,
        source: str,
        fused_count: int,
        sensor_count: int,
        timestamp: datetime,
    ) -> None:
        """Publish a DataFusionCompleted event to the fusion exchange."""
        if not self._channel:
            return

        try:
            exchange = await self._channel.declare_exchange(
                self.FUSION_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            event = {
                "event_id": str(uuid4()),
                "event_type": "data.fusion.completed",
                "occurred_at": datetime.utcnow().isoformat(),
                "source": source,
                "fused_data_points": fused_count,
                "sensor_readings_used": sensor_count,
                "observation_time": timestamp.isoformat(),
            }
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key="data.fusion.completed",
            )
            logger.debug("Published DataFusionCompleted event")
        except Exception as e:
            logger.warning("Failed to publish fusion event: %s", e)


# =====================================================================
# Sensor Reading Consumer — cross-validates sensor vs satellite
# =====================================================================


class SensorReadingConsumer:
    """Consumes sensor reading events for cross-validation against
    satellite data.

    Listens to ``sensor.reading.created`` on a **separate queue**
    (different from AirQualityEventHandler) so that cross-validation
    runs independently of AQI cache updates.

    When anomalies are detected, publishes ``cross.validation.alert``
    to the ``fusion.events`` exchange.
    """

    EXCHANGE_NAME = "sensor.events"
    QUEUE_NAME = "aq.cross.validation.queue"
    ROUTING_KEY = "sensor.reading.created"
    FUSION_EXCHANGE = "fusion.events"

    def __init__(
        self,
        rabbitmq_url: str,
        satellite_cache: RedisCache,
    ):
        self.rabbitmq_url = rabbitmq_url
        self.satellite_cache = satellite_cache
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._consumer_tag: Optional[str] = None

    async def start(self) -> None:
        """Connect to RabbitMQ and begin consuming sensor events."""
        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        # Declare exchange and queue
        exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        queue = await self._channel.declare_queue(
            self.QUEUE_NAME,
            durable=True,
        )
        await queue.bind(exchange, routing_key=self.ROUTING_KEY)

        # Start consuming
        self._consumer_tag = await queue.consume(self._on_message)
        logger.info(
            "SensorReadingConsumer started — listening on %s",
            self.QUEUE_NAME,
        )

    async def stop(self) -> None:
        """Gracefully stop consuming and close connection."""
        if self._channel:
            try:
                await self._channel.close()
            except Exception:
                pass
        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
        logger.info("SensorReadingConsumer stopped")

    async def _on_message(self, message: aio_pika.IncomingMessage) -> None:
        """Handle an incoming sensor reading event."""
        try:
            event_data = json.loads(message.body.decode())
            await self._cross_validate(event_data)
            await message.ack()
        except json.JSONDecodeError:
            logger.error("Invalid JSON in sensor event — rejecting")
            await message.reject(requeue=False)
        except Exception as e:
            logger.error("Error in cross-validation: %s", e)
            await message.nack(requeue=True)

    async def _cross_validate(self, event_data: Dict[str, Any]) -> None:
        """Cross-validate a sensor reading against cached satellite data.

        Steps:
        1. Extract PM2.5 from the sensor event
        2. Look up cached satellite AOD/PM2.5 for the same location
        3. Run anomaly detection via CrossValidationService
        4. If anomalous, publish a CrossValidationAlert
        """
        from ...domain.services.cross_validator import CrossValidationService

        sensor_id = event_data.get("sensor_id")
        latitude = event_data.get("latitude", 0.0)
        longitude = event_data.get("longitude", 0.0)
        sensor_pm25 = event_data.get("pm25")

        if sensor_pm25 is None or not sensor_id:
            return

        try:
            sensor_pm25 = float(sensor_pm25)
        except (ValueError, TypeError):
            return

        # Look up cached satellite data for this location
        satellite_value = await self._get_satellite_value(latitude, longitude)
        if satellite_value is None:
            logger.debug(
                "No satellite data cached for (%.3f, %.3f) — skipping cross-validation",
                latitude,
                longitude,
            )
            return

        # Run anomaly detection
        validator = CrossValidationService(deviation_threshold=0.3)
        is_anomaly, deviation = validator.detect_anomaly(
            sensor_value=sensor_pm25,
            satellite_value=satellite_value,
        )

        if is_anomaly:
            logger.warning(
                "Anomaly detected for sensor %s: "
                "sensor=%.1f, satellite=%.1f, deviation=%.2f",
                sensor_id,
                sensor_pm25,
                satellite_value,
                deviation,
            )
            await self._publish_cross_validation_alert(
                sensor_id=sensor_id,
                latitude=latitude,
                longitude=longitude,
                sensor_value=sensor_pm25,
                satellite_value=satellite_value,
                deviation=deviation,
            )

    async def _get_satellite_value(
        self, latitude: float, longitude: float
    ) -> Optional[float]:
        """Get cached satellite PM2.5 estimate for a location.

        Checks the AQI cache for fused data at this location.
        Falls back to None if no satellite data is available.
        """
        if not self.satellite_cache:
            return None

        cached = await self.satellite_cache.get_aqi(latitude, longitude, 10.0)
        if cached:
            # Try fused_pm25 first (from satellite fusion), then aqi_value
            fused_pm25 = cached.get("fused_pm25")
            if fused_pm25 is not None:
                return float(fused_pm25)

        return None

    async def _publish_cross_validation_alert(
        self,
        sensor_id: str,
        latitude: float,
        longitude: float,
        sensor_value: float,
        satellite_value: float,
        deviation: float,
    ) -> None:
        """Publish a CrossValidationAlert event."""
        if not self._channel:
            return

        try:
            exchange = await self._channel.declare_exchange(
                self.FUSION_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            event = {
                "event_id": str(uuid4()),
                "event_type": "cross.validation.alert",
                "occurred_at": datetime.utcnow().isoformat(),
                "sensor_id": sensor_id,
                "latitude": latitude,
                "longitude": longitude,
                "sensor_value": sensor_value,
                "satellite_value": satellite_value,
                "deviation": round(deviation, 4),
                "severity": "high" if deviation > 0.5 else "medium",
            }
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(event).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key="cross.validation.alert",
            )
            logger.info(
                "Published CrossValidationAlert for sensor %s (deviation=%.2f)",
                sensor_id,
                deviation,
            )
        except Exception as e:
            logger.warning("Failed to publish cross-validation alert: %s", e)
