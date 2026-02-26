"""Factory application service — orchestrates use cases.

This is the primary entry point for all factory-related operations.  Each
public method represents a single use case and follows the pattern:

    1. Validate input (command / query)
    2. Load or create the domain entity
    3. Execute domain logic
    4. Persist changes
    5. Publish domain events
    6. Return a DTO
"""
from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from ...domain.entities.factory import Factory
from ...domain.exceptions.factory_exceptions import (
    FactoryAlreadyExistsError,
    FactoryNotFoundError,
)
from ...domain.repositories.factory_repository import FactoryRepository
from ..commands.create_factory_command import CreateFactoryCommand
from ..commands.resume_factory_command import ResumeFactoryCommand
from ..commands.suspend_factory_command import SuspendFactoryCommand
from ..commands.update_factory_command import UpdateFactoryCommand
from ..dto.factory_dto import FactoryDTO, FactoryListDTO
from ..interfaces.event_publisher import EventPublisher
from ..queries.list_factories_query import ListFactoriesQuery

logger = logging.getLogger(__name__)


class FactoryApplicationService:
    """Orchestrates factory-related use cases.

    Depends on two ports injected at construction time:

    * ``factory_repository`` — persistence abstraction (domain layer)
    * ``event_publisher`` — messaging abstraction (application layer)
    """

    def __init__(
        self,
        factory_repository: FactoryRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = factory_repository
        self._publisher = event_publisher

    # ------------------------------------------------------------------
    # Command handlers (write operations)
    # ------------------------------------------------------------------
    async def create_factory(self, command: CreateFactoryCommand) -> FactoryDTO:
        """Use case: register a new factory.

        Steps:
            1. Validate the command payload.
            2. Check for duplicate registration number.
            3. Create the domain entity (emits ``FactoryCreated``).
            4. Persist via repository.
            5. Publish events.
            6. Return DTO.
        """
        command.validate()

        existing = await self._repo.get_by_registration_number(
            command.registration_number,
        )
        if existing:
            raise FactoryAlreadyExistsError(command.registration_number)

        factory = Factory.create(
            name=command.name,
            registration_number=command.registration_number,
            industry_type=command.industry_type,
            latitude=command.latitude,
            longitude=command.longitude,
            emission_limits=command.emission_limits,
        )

        saved = await self._repo.save(factory)
        await self._publish_events(saved)

        logger.info("Factory created: %s (%s)", saved.id, saved.name)
        return FactoryDTO.from_entity(saved)

    async def update_factory(self, command: UpdateFactoryCommand) -> FactoryDTO:
        """Use case: update mutable factory fields.

        Steps:
            1. Validate the command payload.
            2. Load the existing factory.
            3. Apply partial updates via entity's ``update()`` method.
            4. Persist changes.
            5. Publish events (``FactoryUpdated``).
            6. Return DTO.
        """
        command.validate()

        if not command.has_changes():
            raise ValueError("No fields to update")

        factory = await self._get_factory_or_raise(command.factory_id)

        update_fields = {}
        if command.name is not None:
            update_fields["name"] = command.name
        if command.industry_type is not None:
            update_fields["industry_type"] = command.industry_type
        if command.emission_limits is not None:
            update_fields["emission_limits"] = command.emission_limits
        if command.latitude is not None or command.longitude is not None:
            update_fields["location"] = {
                "latitude": (
                    command.latitude
                    if command.latitude is not None
                    else factory.location.latitude
                ),
                "longitude": (
                    command.longitude
                    if command.longitude is not None
                    else factory.location.longitude
                ),
            }

        factory.update(**update_fields)

        saved = await self._repo.save(factory)
        await self._publish_events(saved)

        logger.info("Factory updated: %s", saved.id)
        return FactoryDTO.from_entity(saved)

    async def suspend_factory(self, command: SuspendFactoryCommand) -> FactoryDTO:
        """Use case: suspend factory operations.

        Steps:
            1. Validate the command.
            2. Load the factory.
            3. Call ``factory.suspend()`` (domain enforces status rules).
            4. Persist.
            5. Publish ``FactoryStatusChanged`` + ``FactorySuspended``.
            6. Return DTO.
        """
        command.validate()

        factory = await self._get_factory_or_raise(command.factory_id)
        factory.suspend(reason=command.reason, suspended_by=command.suspended_by)

        saved = await self._repo.save(factory)
        await self._publish_events(saved)

        logger.info(
            "Factory suspended: %s, reason: %s", saved.id, command.reason,
        )
        return FactoryDTO.from_entity(saved)

    async def resume_factory(self, command: ResumeFactoryCommand) -> FactoryDTO:
        """Use case: resume a suspended factory.

        Steps:
            1. Load the factory.
            2. Call ``factory.resume()`` (domain enforces status rules).
            3. Persist.
            4. Publish ``FactoryStatusChanged`` + ``FactoryResumed``.
            5. Return DTO.
        """
        factory = await self._get_factory_or_raise(command.factory_id)
        factory.resume(resumed_by=command.resumed_by, notes=command.notes)

        saved = await self._repo.save(factory)
        await self._publish_events(saved)

        logger.info("Factory resumed: %s", saved.id)
        return FactoryDTO.from_entity(saved)

    async def delete_factory(self, factory_id: UUID) -> bool:
        """Use case: permanently delete a factory.

        Steps:
            1. Verify the factory exists.
            2. Delete via repository.
            3. Return success status.

        Raises ``FactoryNotFoundError`` if the factory does not exist.
        """
        await self._get_factory_or_raise(factory_id)

        deleted = await self._repo.delete(factory_id)
        if deleted:
            logger.info("Factory deleted: %s", factory_id)
        return deleted

    # ------------------------------------------------------------------
    # Query handlers (read operations)
    # ------------------------------------------------------------------
    async def get_factory(self, factory_id: UUID) -> FactoryDTO:
        """Use case: get a single factory by ID.

        Raises ``FactoryNotFoundError`` if the factory does not exist.
        """
        factory = await self._get_factory_or_raise(factory_id)
        return FactoryDTO.from_entity(factory)

    async def list_factories(self, query: ListFactoriesQuery) -> FactoryListDTO:
        """Use case: list factories with optional filters and pagination.

        Returns a ``FactoryListDTO`` containing the items and total count.
        """
        query.validate()

        factories = await self._repo.list_all(
            status=query.status,
            skip=query.skip,
            limit=query.limit,
        )
        total = await self._repo.count(status=query.status)

        return FactoryListDTO(
            items=[FactoryDTO.from_entity(f) for f in factories],
            total=total,
            skip=query.skip,
            limit=query.limit,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _get_factory_or_raise(self, factory_id: UUID) -> Factory:
        """Load a factory by ID or raise ``FactoryNotFoundError``."""
        factory = await self._repo.get_by_id(factory_id)
        if factory is None:
            raise FactoryNotFoundError(str(factory_id))
        return factory

    async def _publish_events(self, factory: Factory) -> None:
        """Collect and publish all pending domain events from the entity."""
        for event in factory.collect_events():
            try:
                await self._publisher.publish(event)
            except Exception:
                logger.exception(
                    "Failed to publish event %s for factory %s",
                    type(event).__name__,
                    factory.id,
                )
