"""Inbound event handlers for the factory service.

Processes events published by other bounded contexts (alert-service,
sensor-service) that affect factory state.

Events consumed:
    ``alert.violation.detected``  → Update factory status based on severity.
    ``sensor.status.changed``     → Log / react to sensor lifecycle changes.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.value_objects.factory_status import FactoryStatus
from ..persistence.factory_repository_impl import SQLAlchemyFactoryRepository
from ..persistence.database import get_session_maker

logger = logging.getLogger(__name__)

# Type alias matching the shared consumer's handler signature.
EventHandler = Callable[
    [Dict[str, Any], Any],
    Coroutine[Any, Any, None],
]


class FactoryEventHandler:
    """Handles inbound events that affect factory state.

    Each handler method receives the deserialized event payload and the
    raw ``aio_pika`` message.  The handler is responsible for acking
    the message after successful processing.
    """

    # ------------------------------------------------------------------
    # alert.violation.detected
    # ------------------------------------------------------------------
    @staticmethod
    async def handle_violation_detected(
        event_data: Dict[str, Any],
        message: Any,
    ) -> None:
        """React to a violation detected by the alert service.

        If the violation severity is ``critical`` the factory is
        automatically moved to ``CRITICAL`` status.  For ``high``
        severity it moves to ``WARNING``.
        """
        factory_id_raw = event_data.get("factory_id")
        severity = event_data.get("severity", "").lower()

        if not factory_id_raw:
            logger.warning("ViolationDetected missing factory_id — acking")
            await message.ack()
            return

        try:
            factory_id = UUID(factory_id_raw)
        except (ValueError, TypeError):
            logger.error("Invalid factory_id in ViolationDetected: %s", factory_id_raw)
            await message.reject(requeue=False)
            return

        async with get_session_maker()() as session:
            repo = SQLAlchemyFactoryRepository(session)
            factory = await repo.get_by_id(factory_id)

            if factory is None:
                logger.warning(
                    "Factory %s not found for ViolationDetected — acking",
                    factory_id,
                )
                await message.ack()
                return

            # Only update operational factories.
            if not factory.status.is_operational:
                logger.info(
                    "Factory %s is %s — skipping violation status update",
                    factory_id,
                    factory.status.value,
                )
                await message.ack()
                return

            # Map severity to target status.
            status_map: Dict[str, FactoryStatus] = {
                "critical": FactoryStatus.CRITICAL,
                "high": FactoryStatus.WARNING,
            }
            target_status = status_map.get(severity)

            if target_status and target_status != factory.status:
                old_status = factory.status
                factory.status = target_status
                await repo.save(factory)
                await session.commit()
                logger.info(
                    "Factory %s status changed %s → %s (violation severity=%s)",
                    factory_id,
                    old_status.value,
                    target_status.value,
                    severity,
                )
            else:
                logger.debug(
                    "Factory %s: no status change for severity=%s",
                    factory_id,
                    severity,
                )

        await message.ack()

    # ------------------------------------------------------------------
    # sensor.status.changed
    # ------------------------------------------------------------------
    @staticmethod
    async def handle_sensor_status_changed(
        event_data: Dict[str, Any],
        message: Any,
    ) -> None:
        """React to a sensor status change.

        Currently logs the event for observability.  Can be extended to
        trigger alerts if too many sensors go offline for a factory.
        """
        sensor_id = event_data.get("sensor_id")
        factory_id = event_data.get("factory_id")
        new_status = event_data.get("new_status")

        logger.info(
            "Sensor %s (factory %s) status changed to %s",
            sensor_id,
            factory_id,
            new_status,
        )

        await message.ack()

    # ------------------------------------------------------------------
    # Handler registry
    # ------------------------------------------------------------------
    def get_handlers(self) -> Dict[str, EventHandler]:
        """Return a mapping of queue name → handler for ``subscribe_bindings``.

        Queue names match the constants defined in
        ``shared.messaging.config``.
        """
        from shared.messaging.config import (
            FACTORY_SENSOR_STATUS_QUEUE,
            FACTORY_VIOLATION_QUEUE,
        )

        return {
            FACTORY_VIOLATION_QUEUE: self.handle_violation_detected,
            FACTORY_SENSOR_STATUS_QUEUE: self.handle_sensor_status_changed,
        }
