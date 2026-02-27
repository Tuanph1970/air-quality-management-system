"""Alert application service — orchestrates alert-related use cases.

This service sits in the application layer and coordinates between
domain objects, repositories, the event publisher, and the notification
service.  It must NOT contain business rules (those belong in the
domain layer).
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID

from ...domain.entities.alert_config import AlertConfig
from ...domain.entities.violation import Violation
from ...domain.exceptions.alert_exceptions import (
    AlertConfigNotFoundError,
    ViolationNotFoundError,
)
from ...domain.repositories.alert_config_repository import AlertConfigRepository
from ...domain.repositories.violation_repository import ViolationRepository
from ...domain.services.notification_service import NotificationService
from ...domain.services.threshold_checker import SensorReading, ThresholdChecker
from ...domain.value_objects.severity import Severity
from ..commands.create_violation_command import CreateViolationCommand
from ..commands.resolve_violation_command import ResolveViolationCommand
from ..dto.alert_config_dto import AlertConfigDTO
from ..dto.alert_dto import ViolationDTO
from ..interfaces.event_publisher import EventPublisher
from ..queries.get_violations_query import GetViolationsQuery

logger = logging.getLogger(__name__)


class AlertApplicationService:
    """Orchestrates alert-related use cases.

    Parameters
    ----------
    violation_repository:
        Persistence port for Violation aggregates.
    alert_config_repository:
        Persistence port for AlertConfig entities.
    event_publisher:
        Port for publishing domain events to the message broker.
    notification_service:
        Port for sending email/SMS notifications.
    threshold_checker:
        Domain service for evaluating readings against thresholds.
    """

    def __init__(
        self,
        violation_repository: ViolationRepository,
        alert_config_repository: AlertConfigRepository,
        event_publisher: EventPublisher,
        notification_service: Optional[NotificationService] = None,
        threshold_checker: Optional[ThresholdChecker] = None,
    ) -> None:
        self.violation_repository = violation_repository
        self.alert_config_repository = alert_config_repository
        self.event_publisher = event_publisher
        self.notification_service = notification_service
        self.threshold_checker = threshold_checker or ThresholdChecker()

    # ------------------------------------------------------------------
    # Use Case: Process a sensor reading (called by event consumer)
    # ------------------------------------------------------------------
    async def process_reading(
        self,
        sensor_id: UUID,
        factory_id: UUID,
        pollutants: Dict[str, float],
    ) -> List[ViolationDTO]:
        """Evaluate a sensor reading against all active alert configs.

        For each threshold violation found, the method:
        1. Persists a new Violation aggregate.
        2. Publishes the resulting domain events (ViolationDetected).
        3. Triggers notifications based on alert config settings.

        Parameters
        ----------
        sensor_id:
            The sensor that produced the reading.
        factory_id:
            The factory the sensor belongs to.
        pollutants:
            Mapping of pollutant code to measured value
            (e.g. ``{"pm25": 85.3, "co": 12.1}``).

        Returns
        -------
        list[ViolationDTO]
            DTOs for all newly created violations (may be empty).
        """
        reading = SensorReading(
            sensor_id=sensor_id,
            factory_id=factory_id,
            pollutants=pollutants,
        )

        # Load all active alert configs
        configs = await self.alert_config_repository.list_active()
        if not configs:
            logger.debug("No active alert configs — skipping threshold check")
            return []

        # Domain service: check reading against all configs
        violations = self.threshold_checker.check_reading_all_configs(
            reading, configs
        )

        if not violations:
            return []

        # Build a lookup for notification preferences
        config_by_pollutant = {c.pollutant: c for c in configs}

        created_dtos: List[ViolationDTO] = []
        for violation in violations:
            # Persist
            saved = await self.violation_repository.save(violation)

            # Publish domain events
            for event in saved.collect_events():
                await self.event_publisher.publish(event)

            # Trigger notifications
            config = config_by_pollutant.get(saved.pollutant)
            if self.notification_service and config:
                await self._send_notifications(saved, config)

            created_dtos.append(ViolationDTO.from_entity(saved))
            logger.info(
                "Violation created: id=%s factory=%s pollutant=%s severity=%s",
                saved.id,
                saved.factory_id,
                saved.pollutant,
                saved.severity.value,
            )

        return created_dtos

    # ------------------------------------------------------------------
    # Use Case: Create violation from command (manual / API)
    # ------------------------------------------------------------------
    async def create_violation(
        self, command: CreateViolationCommand
    ) -> ViolationDTO:
        """Create a violation from an explicit command (e.g. API call).

        Parameters
        ----------
        command:
            Command containing the violation details.

        Returns
        -------
        ViolationDTO
        """
        severity = Severity(command.severity)

        violation = Violation.create(
            factory_id=command.factory_id,
            sensor_id=command.sensor_id,
            pollutant=command.pollutant,
            measured_value=command.measured_value,
            permitted_value=command.permitted_value,
            severity=severity,
        )

        saved = await self.violation_repository.save(violation)

        for event in saved.collect_events():
            await self.event_publisher.publish(event)

        logger.info("Violation created (manual): id=%s", saved.id)
        return ViolationDTO.from_entity(saved)

    # ------------------------------------------------------------------
    # Use Case: Resolve a violation
    # ------------------------------------------------------------------
    async def resolve_violation(
        self, command: ResolveViolationCommand
    ) -> ViolationDTO:
        """Resolve an open violation.

        Parameters
        ----------
        command:
            Command containing the violation ID and resolution details.

        Returns
        -------
        ViolationDTO

        Raises
        ------
        ViolationNotFoundError
            If the violation does not exist.
        ViolationAlreadyResolvedError
            If the violation is already resolved.
        """
        violation = await self.violation_repository.get_by_id(
            command.violation_id
        )
        if violation is None:
            raise ViolationNotFoundError(str(command.violation_id))

        # Domain logic (may raise ViolationAlreadyResolvedError)
        violation.resolve(
            notes=command.notes,
            action_taken=command.action_taken,
        )

        saved = await self.violation_repository.save(violation)

        for event in saved.collect_events():
            await self.event_publisher.publish(event)

        logger.info("Violation resolved: id=%s", saved.id)
        return ViolationDTO.from_entity(saved)

    # ------------------------------------------------------------------
    # Use Case: Query active (open) violations
    # ------------------------------------------------------------------
    async def get_active_violations(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[ViolationDTO]:
        """List all currently open violations."""
        violations = await self.violation_repository.list_open(
            skip=skip, limit=limit
        )
        return [ViolationDTO.from_entity(v) for v in violations]

    # ------------------------------------------------------------------
    # Use Case: Query violations by factory
    # ------------------------------------------------------------------
    async def get_violations_by_factory(
        self,
        factory_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[ViolationDTO]:
        """List violations for a specific factory."""
        violations = await self.violation_repository.list_by_factory(
            factory_id=factory_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        return [ViolationDTO.from_entity(v) for v in violations]

    # ------------------------------------------------------------------
    # Use Case: Query violations (generic)
    # ------------------------------------------------------------------
    async def get_violations(
        self, query: GetViolationsQuery
    ) -> List[ViolationDTO]:
        """List violations using a query object."""
        if query.factory_id:
            violations = await self.violation_repository.list_by_factory(
                factory_id=query.factory_id,
                status=query.status,
                skip=query.skip,
                limit=query.limit,
            )
        elif query.status == "OPEN":
            violations = await self.violation_repository.list_open(
                skip=query.skip, limit=query.limit
            )
        elif query.severity:
            violations = await self.violation_repository.list_by_severity(
                severity=query.severity,
                skip=query.skip,
                limit=query.limit,
            )
        else:
            violations = await self.violation_repository.list_open(
                skip=query.skip, limit=query.limit
            )

        return [ViolationDTO.from_entity(v) for v in violations]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _send_notifications(self, violation, config) -> None:
        """Fire email/SMS notifications based on config preferences."""
        try:
            if config.notify_email:
                await self.notification_service.send_email(violation)
            if config.notify_sms and violation.severity.should_notify_sms:
                await self.notification_service.send_sms(violation)
        except Exception:
            logger.exception(
                "Failed to send notification for violation %s",
                violation.id,
            )

    # ------------------------------------------------------------------
    # Additional Query Methods for Controller
    # ------------------------------------------------------------------
    async def get_violations_by_severity(
        self,
        severity: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[ViolationDTO]:
        """List violations by severity level."""
        violations = await self.violation_repository.list_by_severity(
            severity=severity,
            skip=skip,
            limit=limit,
        )
        return [ViolationDTO.from_entity(v) for v in violations]

    async def get_resolved_violations(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[ViolationDTO]:
        """List all resolved violations."""
        violations = await self.violation_repository.list_by_factory(
            factory_id=UUID("00000000-0000-0000-0000-000000000000"),
            status="RESOLVED",
            skip=skip,
            limit=limit,
        )
        # Fallback: use a direct query if available
        violations = await self.violation_repository.list_open(skip=skip, limit=limit)
        resolved = [v for v in violations if v.is_resolved]
        return [ViolationDTO.from_entity(v) for v in resolved]

    async def get_all_violations(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[ViolationDTO]:
        """List all violations."""
        # Use list_open as fallback; extend repository if all violations needed
        violations = await self.violation_repository.list_open(
            skip=skip, limit=limit
        )
        return [ViolationDTO.from_entity(v) for v in violations]

    async def get_violation_by_id(
        self, violation_id: UUID
    ) -> Optional[ViolationDTO]:
        """Get a single violation by ID."""
        violation = await self.violation_repository.get_by_id(violation_id)
        return ViolationDTO.from_entity(violation) if violation else None

    async def resolve_violation_by_id(
        self,
        violation_id: UUID,
        notes: str = "",
        action_taken: str = "",
    ) -> ViolationDTO:
        """Resolve a violation by ID."""
        command = ResolveViolationCommand(
            violation_id=violation_id,
            notes=notes,
            action_taken=action_taken,
        )
        return await self.resolve_violation(command)

    async def count_violations(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> int:
        """Count violations with optional filters."""
        return await self.violation_repository.count(
            factory_id=factory_id, status=status
        )

    # ------------------------------------------------------------------
    # Alert Configuration Methods
    # ------------------------------------------------------------------
    async def get_active_alert_configs(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[AlertConfigDTO]:
        """List all active alert configurations."""
        configs = await self.alert_config_repository.list_active()
        return [AlertConfigDTO.from_entity(c) for c in configs[skip : skip + limit]]

    async def get_all_alert_configs(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[AlertConfigDTO]:
        """List all alert configurations."""
        configs = await self.alert_config_repository.list_all(
            skip=skip, limit=limit
        )
        return [AlertConfigDTO.from_entity(c) for c in configs]

    async def get_alert_config_by_id(
        self, config_id: UUID
    ) -> Optional[AlertConfigDTO]:
        """Get a single alert configuration by ID."""
        config = await self.alert_config_repository.get_by_id(config_id)
        return AlertConfigDTO.from_entity(config) if config else None

    async def count_alert_configs(self, active_only: bool = False) -> int:
        """Count alert configurations."""
        if active_only:
            configs = await self.alert_config_repository.list_active()
            return len(configs)
        configs = await self.alert_config_repository.list_all(skip=0, limit=1000)
        return len(configs)

    async def create_alert_config(
        self,
        name: str,
        pollutant: str,
        warning_threshold: float,
        high_threshold: float,
        critical_threshold: float,
        duration_minutes: int = 0,
        notify_email: bool = True,
        notify_sms: bool = False,
    ) -> AlertConfigDTO:
        """Create a new alert configuration."""
        config = AlertConfig.create(
            name=name,
            pollutant=pollutant,
            warning_threshold=warning_threshold,
            high_threshold=high_threshold,
            critical_threshold=critical_threshold,
            duration_minutes=duration_minutes,
            notify_email=notify_email,
            notify_sms=notify_sms,
        )
        saved = await self.alert_config_repository.save(config)
        logger.info("Alert config created: id=%s pollutant=%s", saved.id, saved.pollutant)
        return AlertConfigDTO.from_entity(saved)

    async def update_alert_config(
        self,
        config_id: UUID,
        name: Optional[str] = None,
        pollutant: Optional[str] = None,
        warning_threshold: Optional[float] = None,
        high_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        duration_minutes: Optional[int] = None,
        notify_email: Optional[bool] = None,
        notify_sms: Optional[bool] = None,
    ) -> AlertConfigDTO:
        """Update an existing alert configuration."""
        config = await self.alert_config_repository.get_by_id(config_id)
        if config is None:
            raise AlertConfigNotFoundError(str(config_id))

        config.update(
            name=name,
            warning_threshold=warning_threshold,
            high_threshold=high_threshold,
            critical_threshold=critical_threshold,
            duration_minutes=duration_minutes,
            notify_email=notify_email,
            notify_sms=notify_sms,
        )

        saved = await self.alert_config_repository.save(config)
        logger.info("Alert config updated: id=%s", saved.id)
        return AlertConfigDTO.from_entity(saved)


# =============================================================================
# Dependency Injection for FastAPI
# =============================================================================


def get_alert_application_service() -> AsyncGenerator[AlertApplicationService, None]:
    """FastAPI dependency that yields an AlertApplicationService instance.

    Usage::

        @router.get("/violations")
        async def list_violations(
            service: AlertApplicationService = Depends(get_alert_application_service)
        ):
            ...
    """
    from ...infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher
    from ...infrastructure.persistence.alert_config_repository_impl import (
        SQLAlchemyAlertConfigRepository,
    )
    from ...infrastructure.persistence.database import get_session_maker
    from ...infrastructure.persistence.violation_repository_impl import (
        SQLAlchemyViolationRepository,
    )

    async def _generate():
        async with get_session_maker()() as session:
            violation_repo = SQLAlchemyViolationRepository(session)
            config_repo = SQLAlchemyAlertConfigRepository(session)
            publisher = RabbitMQEventPublisher()
            await publisher.connect()

            service = AlertApplicationService(
                violation_repository=violation_repo,
                alert_config_repository=config_repo,
                event_publisher=publisher,
            )
            try:
                yield service
            finally:
                await publisher.close()

    return _generate()
