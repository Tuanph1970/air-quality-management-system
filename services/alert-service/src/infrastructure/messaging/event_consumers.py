"""Inbound event handlers for the alert service.

Processes events published by other bounded contexts (sensor-service,
factory-service) that drive the alert workflow.

Events consumed:
    ``sensor.reading.created``  → Check thresholds, create violations.
    ``factory.status.changed``  → Log factory status transitions.

The ``AlertEventHandler`` follows the same pattern as the factory
service's ``FactoryEventHandler``: static async methods that receive
deserialized event data and the raw ``aio_pika`` message, paired with a
``get_handlers()`` registry for ``subscribe_bindings()``.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine, Dict
from uuid import UUID

from ..persistence.alert_config_repository_impl import (
    SQLAlchemyAlertConfigRepository,
)
from ..persistence.database import get_session_maker
from ..persistence.violation_repository_impl import (
    SQLAlchemyViolationRepository,
)
from .rabbitmq_publisher import RabbitMQEventPublisher

logger = logging.getLogger(__name__)

# Type alias matching the shared consumer's handler signature.
EventHandler = Callable[
    [Dict[str, Any], Any],
    Coroutine[Any, Any, None],
]

# Module-level publisher — connected once at startup, reused by handlers.
_publisher: RabbitMQEventPublisher | None = None


def set_publisher(publisher: RabbitMQEventPublisher) -> None:
    """Inject the shared publisher instance (called during lifespan)."""
    global _publisher
    _publisher = publisher


class AlertEventHandler:
    """Handles inbound events that drive the alert workflow.

    Each handler method receives the deserialized event payload and the
    raw ``aio_pika`` message.  The handler is responsible for acking
    the message after successful processing.
    """

    # ------------------------------------------------------------------
    # sensor.reading.created
    # ------------------------------------------------------------------
    @staticmethod
    async def handle_sensor_reading(
        event_data: Dict[str, Any],
        message: Any,
    ) -> None:
        """Process an incoming sensor reading and check thresholds.

        Flow:
        1. Parse the sensor reading event.
        2. Load all active alert configurations from the database.
        3. Use the ``ThresholdChecker`` domain service to evaluate.
        4. For each violation found:
           a. Persist the ``Violation`` aggregate.
           b. Publish ``ViolationDetected`` domain events.
        5. Ack the message.
        """
        from ...application.services.alert_application_service import (
            AlertApplicationService,
        )
        from ...domain.services.threshold_checker import ThresholdChecker

        sensor_id_raw = event_data.get("sensor_id")
        factory_id_raw = event_data.get("factory_id")

        if not sensor_id_raw or not factory_id_raw:
            logger.warning(
                "SensorReadingCreated missing sensor_id or factory_id — acking"
            )
            await message.ack()
            return

        try:
            sensor_id = UUID(str(sensor_id_raw))
            factory_id = UUID(str(factory_id_raw))
        except (ValueError, TypeError) as exc:
            logger.error(
                "Invalid UUID in SensorReadingCreated: %s — rejecting", exc
            )
            await message.reject(requeue=False)
            return

        # Build pollutant map from event data
        pollutants: Dict[str, float] = {}
        for key in ("pm25", "pm10", "co", "no2", "so2", "o3"):
            value = event_data.get(key)
            if value is not None:
                try:
                    pollutants[key] = float(value)
                except (ValueError, TypeError):
                    logger.warning(
                        "Invalid %s value in reading: %s — skipping",
                        key,
                        value,
                    )

        if not pollutants:
            logger.debug(
                "SensorReadingCreated has no valid pollutant values — acking"
            )
            await message.ack()
            return

        # Process the reading through the application service
        async with get_session_maker()() as session:
            violation_repo = SQLAlchemyViolationRepository(session)
            config_repo = SQLAlchemyAlertConfigRepository(session)

            app_service = AlertApplicationService(
                violation_repository=violation_repo,
                alert_config_repository=config_repo,
                event_publisher=_publisher,
                threshold_checker=ThresholdChecker(),
            )

            try:
                violations = await app_service.process_reading(
                    sensor_id=sensor_id,
                    factory_id=factory_id,
                    pollutants=pollutants,
                )

                if violations:
                    logger.info(
                        "Created %d violation(s) for factory %s from sensor %s",
                        len(violations),
                        factory_id,
                        sensor_id,
                    )
                else:
                    logger.debug(
                        "No violations for reading from sensor %s",
                        sensor_id,
                    )
            except Exception:
                logger.exception(
                    "Error processing sensor reading from sensor %s",
                    sensor_id,
                )
                # Nack is handled by the shared consumer's _dispatch
                raise

        await message.ack()

    # ------------------------------------------------------------------
    # factory.status.changed
    # ------------------------------------------------------------------
    @staticmethod
    async def handle_factory_status_changed(
        event_data: Dict[str, Any],
        message: Any,
    ) -> None:
        """React to a factory status change.

        Currently logs the event for observability.  Can be extended to
        auto-resolve violations when a factory is suspended or to adjust
        alert thresholds based on factory status.
        """
        factory_id = event_data.get("factory_id")
        old_status = event_data.get("old_status")
        new_status = event_data.get("new_status")
        reason = event_data.get("reason", "")

        logger.info(
            "Factory %s status changed %s → %s (reason: %s)",
            factory_id,
            old_status,
            new_status,
            reason,
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
            ALERT_FACTORY_EVENTS_QUEUE,
            ALERT_SENSOR_READINGS_QUEUE,
        )

        return {
            ALERT_SENSOR_READINGS_QUEUE: self.handle_sensor_reading,
            ALERT_FACTORY_EVENTS_QUEUE: self.handle_factory_status_changed,
        }
