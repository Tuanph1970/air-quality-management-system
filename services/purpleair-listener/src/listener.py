"""PurpleAir Event Listener Service.

This service consumes PurpleAir events from RabbitMQ and synchronizes
them with the sensor-service by:
1. Registering PurpleAir sensors in sensor-service
2. Submitting sensor readings to sensor-service

This follows the event-driven architecture pattern, keeping services decoupled.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import aio_pika
import httpx
from aio_pika import IncomingMessage
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


class PurpleAirEventListener:
    """Listen for PurpleAir events and sync with sensor-service."""

    def __init__(
        self,
        rabbitmq_url: str,
        sensor_service_url: str,
    ):
        self.rabbitmq_url = rabbitmq_url
        self.sensor_service_url = sensor_service_url.rstrip("/")
        self._connection: Optional[AbstractConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._queue: Optional[AbstractQueue] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._running = False

        # Sensor cache to avoid repeated API calls
        self._registered_sensors: Dict[int, str] = {}  # purpleair_id -> internal UUID

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.sensor_service_url,
                timeout=30.0,
            )
        return self._http_client

    async def _connect_rabbitmq(self) -> None:
        """Connect to RabbitMQ and set up queue."""
        logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_url}")

        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()

        # Set QoS
        await self._channel.set_qos(prefetch_count=10)

        # Declare queue (same name as publisher uses for routing)
        self._queue = await self._channel.declare_queue(
            "purpleair.events",
            durable=True,
            auto_delete=False,
        )

        logger.info("RabbitMQ connection established")

    async def _register_sensor(
        self,
        purpleair_sensor_id: int,
        latitude: float,
        longitude: float,
    ) -> Optional[str]:
        """Register a PurpleAir sensor in sensor-service.

        Returns:
            Internal sensor UUID if successful, None otherwise
        """
        try:
            client = await self._get_http_client()

            # Generate a unique serial number for PurpleAir sensors
            serial_number = f"PURPLEAIR-{purpleair_sensor_id}"

            # Check if sensor already exists
            try:
                # Try to get existing sensor by listing and filtering
                response = await client.get("/sensors")
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        if item.get("serial_number") == serial_number:
                            sensor_id = item.get("id")
                            logger.info(
                                f"Found existing sensor {purpleair_sensor_id} "
                                f"with internal ID {sensor_id}"
                            )
                            self._registered_sensors[purpleair_sensor_id] = sensor_id
                            return sensor_id
            except Exception as e:
                logger.warning(f"Error checking existing sensors: {e}")

            # Register new sensor
            payload = {
                "serial_number": serial_number,
                "sensor_type": "LOW_COST_PM",
                "model": "PurpleAir Flex",
                "latitude": latitude,
                "longitude": longitude,
                "calibration_params": {},
            }

            logger.info(
                f"Registering PurpleAir sensor {purpleair_sensor_id} "
                f"with serial {serial_number}"
            )

            response = await client.post("/sensors", json=payload)

            if response.status_code in (200, 201):
                result = response.json()
                sensor_id = result.get("id")
                logger.info(
                    f"Successfully registered sensor {purpleair_sensor_id} "
                    f"with internal ID {sensor_id}"
                )
                self._registered_sensors[purpleair_sensor_id] = sensor_id
                return sensor_id
            elif response.status_code == 409:
                # Conflict - sensor already exists
                logger.warning(
                    f"Sensor {purpleair_sensor_id} already exists (409 conflict)"
                )
                # Try to find it again
                response = await client.get("/sensors")
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        if item.get("serial_number") == serial_number:
                            sensor_id = item.get("id")
                            self._registered_sensors[purpleair_sensor_id] = sensor_id
                            return sensor_id
            else:
                logger.error(
                    f"Failed to register sensor {purpleair_sensor_id}: "
                    f"{response.status_code} - {response.text}"
                )

            return None

        except Exception as e:
            logger.error(f"Error registering sensor {purpleair_sensor_id}: {e}", exc_info=True)
            return None

    async def _submit_reading(
        self,
        internal_sensor_id: str,
        readings: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Submit a reading to sensor-service.

        Args:
            internal_sensor_id: Internal sensor UUID
            readings: Reading values (PM25, PM10, etc.)
            timestamp: Optional timestamp

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_http_client()

            # Map PurpleAir readings to sensor-service format
            payload = {
                "pm25": readings.get("PM25", 0.0),
                "pm10": readings.get("PM10", 0.0),
                "co": readings.get("CO", 0.0),
                "no2": readings.get("NO2", 0.0),
                "o3": readings.get("O3", 0.0),
                "so2": readings.get("SO2", 0.0),
                "temperature": readings.get("temperature", 0.0),
                "humidity": readings.get("humidity", 0.0),
            }

            if timestamp:
                payload["timestamp"] = timestamp.isoformat()

            endpoint = f"/sensors/{internal_sensor_id}/readings"
            response = await client.post(endpoint, json=payload)

            if response.status_code in (200, 201):
                logger.debug(
                    f"Successfully submitted reading for sensor {internal_sensor_id}"
                )
                return True
            else:
                logger.error(
                    f"Failed to submit reading for sensor {internal_sensor_id}: "
                    f"{response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error submitting reading: {e}", exc_info=True)
            return False

    async def _process_event(self, message: IncomingMessage) -> None:
        """Process a PurpleAir event."""
        async with message.process():
            try:
                body = message.body.decode()
                data = json.loads(body)

                event_type = data.get("event_type", "")
                logger.debug(f"Processing event: {event_type}")

                if event_type == "purpleair.data.ingested":
                    await self._handle_data_ingested(data)
                else:
                    logger.debug(f"Unknown event type: {event_type}")

            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    async def _handle_data_ingested(self, data: Dict[str, Any]) -> None:
        """Handle purpleair.data.ingested event."""
        try:
            purpleair_sensor_id = data.get("purpleair_sensor_id")
            readings = data.get("readings", {})
            latitude = data.get("latitude", 0.0)
            longitude = data.get("longitude", 0.0)
            timestamp_str = data.get("timestamp")

            timestamp = None
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            if not purpleair_sensor_id:
                logger.warning("Missing purpleair_sensor_id in event")
                return

            # Get or register sensor
            internal_sensor_id = self._registered_sensors.get(purpleair_sensor_id)

            if not internal_sensor_id:
                internal_sensor_id = await self._register_sensor(
                    purpleair_sensor_id,
                    latitude,
                    longitude,
                )

            if not internal_sensor_id:
                logger.error(
                    f"Failed to register sensor {purpleair_sensor_id}, "
                    f"skipping reading submission"
                )
                return

            # Submit reading
            await self._submit_reading(internal_sensor_id, readings, timestamp)

            logger.info(
                f"Processed PurpleAir data for sensor {purpleair_sensor_id} "
                f"(internal: {internal_sensor_id}): PM2.5={readings.get('PM25', 'N/A')}"
            )

        except Exception as e:
            logger.error(f"Error handling data.ingested event: {e}", exc_info=True)

    async def start(self) -> None:
        """Start the event listener."""
        logger.info("Starting PurpleAir Event Listener...")

        await self._connect_rabbitmq()

        # Bind queue to exchange
        await self._queue.bind("amq.topic", "purpleair.*")

        self._running = True

        logger.info("Starting event consumption loop...")
        await self._queue.consume(self._process_event)

        # Keep running
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the event listener."""
        logger.info("Stopping PurpleAir Event Listener...")

        self._running = False

        if self._connection:
            await self._connection.close()

        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

        logger.info("PurpleAir Event Listener stopped")


async def main():
    """Main entry point."""
    # Configuration from environment
    rabbitmq_url = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@rabbitmq:5672/",
    )
    sensor_service_url = os.getenv(
        "SENSOR_SERVICE_URL",
        "http://sensor-service:8002",
    )

    listener = PurpleAirEventListener(
        rabbitmq_url=rabbitmq_url,
        sensor_service_url=sensor_service_url,
    )

    try:
        await listener.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await listener.stop()


if __name__ == "__main__":
    asyncio.run(main())
