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
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import aio_pika
import httpx
import uvicorn
from aio_pika import IncomingMessage
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from fastapi import FastAPI
from pydantic import BaseModel

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# ── Shared health state ────────────────────────────────────────────────────────

_health = {"rabbitmq_connected": False, "messages_processed": 0}


def _set_rabbitmq_connected(connected: bool) -> None:
    _health["rabbitmq_connected"] = connected


def _increment_processed() -> None:
    _health["messages_processed"] += 1


# ── FastAPI Health App ────────────────────────────────────────────────────────

_health_app = FastAPI(title="purpleair-listener")


class HealthResponse(BaseModel):
    service: str
    status: str
    rabbitmq_connected: bool
    messages_processed: int


@_health_app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        service="purpleair-listener",
        status="healthy" if _health["rabbitmq_connected"] else "degraded",
        rabbitmq_connected=_health["rabbitmq_connected"],
        messages_processed=_health["messages_processed"],
    )


# ── Listener ──────────────────────────────────────────────────────────────────

_listener: Optional["PurpleAirEventListener"] = None


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
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.sensor_service_url,
                timeout=30.0,
            )
        return self._http_client

    async def _connect_rabbitmq(self) -> None:
        logger.info(f"Connecting to RabbitMQ at {self.rabbitmq_url}")
        self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        self._queue = await self._channel.declare_queue(
            "purpleair.events",
            durable=True,
            auto_delete=False,
        )
        logger.info("RabbitMQ connection established")
        _set_rabbitmq_connected(True)

    async def _register_sensor(
        self,
        purpleair_sensor_id: int,
        latitude: float,
        longitude: float,
    ) -> Optional[str]:
        try:
            client = await self._get_http_client()
            serial_number = f"PURPLEAIR-{purpleair_sensor_id}"

            # Check if already registered
            try:
                response = await client.get("/sensors")
                if response.status_code == 200:
                    for item in response.json().get("items", []):
                        if item.get("serial_number") == serial_number:
                            self._registered_sensors[purpleair_sensor_id] = item["id"]
                            return item["id"]
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

            response = await client.post("/sensors", json=payload)

            if response.status_code in (200, 201):
                sensor_id = response.json().get("id")
                self._registered_sensors[purpleair_sensor_id] = sensor_id
                return sensor_id
            elif response.status_code == 409:
                # Find existing sensor
                response = await client.get("/sensors")
                if response.status_code == 200:
                    for item in response.json().get("items", []):
                        if item.get("serial_number") == serial_number:
                            self._registered_sensors[purpleair_sensor_id] = item["id"]
                            return item["id"]
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
        try:
            client = await self._get_http_client()
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

            response = await client.post(
                f"/sensors/{internal_sensor_id}/readings",
                json=payload,
            )
            return response.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Error submitting reading: {e}", exc_info=True)
            return False

    async def _process_event(self, message: IncomingMessage) -> None:
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                event_type = data.get("event_type", "")

                if event_type == "purpleair.data.ingested":
                    await self._handle_data_ingested(data)
                    _increment_processed()
                else:
                    logger.debug(f"Unknown event type: {event_type}")

            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    async def _handle_data_ingested(self, data: Dict[str, Any]) -> None:
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

            internal_sensor_id = self._registered_sensors.get(purpleair_sensor_id)
            if not internal_sensor_id:
                internal_sensor_id = await self._register_sensor(
                    purpleair_sensor_id, latitude, longitude
                )

            if not internal_sensor_id:
                logger.error(f"Failed to register sensor {purpleair_sensor_id}, skipping")
                return

            await self._submit_reading(internal_sensor_id, readings, timestamp)

            logger.info(
                f"Processed PurpleAir data for sensor {purpleair_sensor_id} "
                f"(internal: {internal_sensor_id}): PM2.5={readings.get('PM25', 'N/A')}"
            )
        except Exception as e:
            logger.error(f"Error handling data.ingested event: {e}", exc_info=True)

    async def start(self) -> None:
        logger.info("Starting PurpleAir Event Listener...")
        await self._connect_rabbitmq()
        await self._queue.bind("amq.topic", "purpleair.*")
        self._running = True
        logger.info("Starting event consumption loop...")
        await self._queue.consume(self._process_event)
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        logger.info("Stopping PurpleAir Event Listener...")
        self._running = False
        if self._connection:
            await self._connection.close()
            _set_rabbitmq_connected(False)
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        logger.info("PurpleAir Event Listener stopped")


# ── FastAPI app with lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _listener
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    sensor_service_url = os.getenv("SENSOR_SERVICE_URL", "http://sensor-service:8002")

    _listener = PurpleAirEventListener(
        rabbitmq_url=rabbitmq_url,
        sensor_service_url=sensor_service_url,
    )

    # Run listener in background task
    listener_task = asyncio.create_task(_listener.start())

    yield

    # Shutdown
    await _listener.stop()
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="purpleair-listener",
    lifespan=lifespan,
)
app.add_api_route("/health", health, response_model=HealthResponse, tags=["health"])


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("HEALTH_PORT", "8012"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
