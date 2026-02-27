"""RabbitMQ event consumers for the remote-sensing service.

Handles inbound events from other services (e.g. sensor readings,
factory status changes) that the remote-sensing service needs to
react to.
"""
from __future__ import annotations

import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)


class RemoteSensingEventHandler:
    """Dispatches inbound domain events to handler methods."""

    def get_handlers(self) -> Dict[str, Callable]:
        """Return a mapping of event_type → handler callable."""
        return {
            "sensor.reading.created": self._handle_sensor_reading,
            "factory.status.changed": self._handle_factory_status_change,
        }

    async def _handle_sensor_reading(self, event: dict) -> None:
        """Handle a new sensor reading — could trigger fusion or calibration."""
        logger.info(
            "Received sensor reading event: sensor_id=%s",
            event.get("sensor_id"),
        )

    async def _handle_factory_status_change(self, event: dict) -> None:
        """Handle factory status change — could update local caches."""
        logger.info(
            "Received factory status change: factory_id=%s status=%s",
            event.get("factory_id"),
            event.get("new_status"),
        )
