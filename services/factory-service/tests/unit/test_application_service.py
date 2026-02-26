"""Unit tests for FactoryApplicationService with mock repo and publisher."""
from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.commands.create_factory_command import CreateFactoryCommand
from src.application.commands.suspend_factory_command import SuspendFactoryCommand
from src.application.dto.factory_dto import FactoryDTO, FactoryListDTO
from src.application.queries.list_factories_query import ListFactoriesQuery
from src.application.services.factory_application_service import (
    FactoryApplicationService,
)
from src.domain.exceptions.factory_exceptions import (
    FactoryAlreadyExistsError,
    FactoryAlreadySuspendedError,
    FactoryNotFoundError,
)


# =========================================================================
# create_factory
# =========================================================================
class TestCreateFactory:
    @pytest.mark.asyncio
    async def test_create_factory_success(self, factory_service, mock_publisher):
        cmd = CreateFactoryCommand(
            name="Test Factory",
            registration_number="REG-001",
            industry_type="Steel",
            latitude=21.0,
            longitude=105.0,
            emission_limits={"pm25_limit": 50.0},
        )
        dto = await factory_service.create_factory(cmd)

        assert isinstance(dto, FactoryDTO)
        assert dto.name == "Test Factory"
        assert dto.registration_number == "REG-001"
        assert dto.status == "ACTIVE"
        assert dto.latitude == 21.0

    @pytest.mark.asyncio
    async def test_create_factory_publishes_events(self, factory_service, mock_publisher):
        cmd = CreateFactoryCommand(
            name="Event Test",
            registration_number="REG-002",
            industry_type="Chemical",
            latitude=10.0,
            longitude=106.0,
        )
        await factory_service.create_factory(cmd)

        assert len(mock_publisher.events) >= 1
        assert any(e.event_type == "factory.created" for e in mock_publisher.events)

    @pytest.mark.asyncio
    async def test_create_duplicate_registration_raises(self, factory_service):
        cmd = CreateFactoryCommand(
            name="First",
            registration_number="REG-DUP",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        await factory_service.create_factory(cmd)

        cmd2 = CreateFactoryCommand(
            name="Second",
            registration_number="REG-DUP",
            industry_type="Chemical",
            latitude=11.0,
            longitude=21.0,
        )
        with pytest.raises(FactoryAlreadyExistsError):
            await factory_service.create_factory(cmd2)

    @pytest.mark.asyncio
    async def test_create_factory_invalid_name_raises(self, factory_service):
        cmd = CreateFactoryCommand(
            name="",
            registration_number="REG-003",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        with pytest.raises(ValueError, match="name"):
            await factory_service.create_factory(cmd)

    @pytest.mark.asyncio
    async def test_create_factory_invalid_latitude_raises(self, factory_service):
        cmd = CreateFactoryCommand(
            name="Test",
            registration_number="REG-004",
            industry_type="Steel",
            latitude=91.0,
            longitude=20.0,
        )
        with pytest.raises(ValueError, match="Latitude"):
            await factory_service.create_factory(cmd)

    @pytest.mark.asyncio
    async def test_create_factory_returns_dto_with_id(self, factory_service):
        cmd = CreateFactoryCommand(
            name="ID Test",
            registration_number="REG-005",
            industry_type="Textile",
            latitude=15.0,
            longitude=100.0,
        )
        dto = await factory_service.create_factory(cmd)
        assert dto.id is not None


# =========================================================================
# suspend_factory
# =========================================================================
class TestSuspendFactory:
    @pytest.mark.asyncio
    async def test_suspend_factory_success(self, factory_service, mock_publisher):
        # Create a factory first
        create_cmd = CreateFactoryCommand(
            name="Suspend Me",
            registration_number="REG-SUSPEND",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        created = await factory_service.create_factory(create_cmd)

        # Suspend it
        suspend_cmd = SuspendFactoryCommand(
            factory_id=created.id,
            reason="Emission violation",
            suspended_by=uuid4(),
        )
        dto = await factory_service.suspend_factory(suspend_cmd)

        assert dto.status == "SUSPENDED"
        assert dto.id == created.id

    @pytest.mark.asyncio
    async def test_suspend_publishes_events(self, factory_service, mock_publisher):
        create_cmd = CreateFactoryCommand(
            name="Event Suspend",
            registration_number="REG-SUSPEND-EVT",
            industry_type="Chemical",
            latitude=10.0,
            longitude=20.0,
        )
        created = await factory_service.create_factory(create_cmd)
        mock_publisher.clear()

        suspend_cmd = SuspendFactoryCommand(
            factory_id=created.id,
            reason="Test reason",
            suspended_by=uuid4(),
        )
        await factory_service.suspend_factory(suspend_cmd)

        event_types = [e.event_type for e in mock_publisher.events]
        assert "factory.status.changed" in event_types
        assert "factory.suspended" in event_types

    @pytest.mark.asyncio
    async def test_suspend_nonexistent_factory_raises(self, factory_service):
        cmd = SuspendFactoryCommand(
            factory_id=uuid4(),
            reason="Test",
            suspended_by=uuid4(),
        )
        with pytest.raises(FactoryNotFoundError):
            await factory_service.suspend_factory(cmd)

    @pytest.mark.asyncio
    async def test_suspend_already_suspended_raises(self, factory_service):
        create_cmd = CreateFactoryCommand(
            name="Double Suspend",
            registration_number="REG-DBL-SUS",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        created = await factory_service.create_factory(create_cmd)

        suspend_cmd = SuspendFactoryCommand(
            factory_id=created.id,
            reason="First",
            suspended_by=uuid4(),
        )
        await factory_service.suspend_factory(suspend_cmd)

        with pytest.raises(FactoryAlreadySuspendedError):
            await factory_service.suspend_factory(suspend_cmd)

    @pytest.mark.asyncio
    async def test_suspend_empty_reason_raises(self, factory_service):
        create_cmd = CreateFactoryCommand(
            name="No Reason",
            registration_number="REG-NOREASON",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        created = await factory_service.create_factory(create_cmd)

        cmd = SuspendFactoryCommand(
            factory_id=created.id,
            reason="",
            suspended_by=uuid4(),
        )
        with pytest.raises(ValueError, match="reason"):
            await factory_service.suspend_factory(cmd)


# =========================================================================
# list_factories
# =========================================================================
class TestListFactories:
    @pytest.mark.asyncio
    async def test_list_empty(self, factory_service):
        query = ListFactoriesQuery()
        result = await factory_service.list_factories(query)

        assert isinstance(result, FactoryListDTO)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_returns_created_factories(self, factory_service):
        for i in range(3):
            cmd = CreateFactoryCommand(
                name=f"Factory {i}",
                registration_number=f"REG-LIST-{i}",
                industry_type="Steel",
                latitude=10.0 + i,
                longitude=20.0 + i,
            )
            await factory_service.create_factory(cmd)

        query = ListFactoriesQuery()
        result = await factory_service.list_factories(query)

        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, factory_service):
        for i in range(5):
            cmd = CreateFactoryCommand(
                name=f"Page Factory {i}",
                registration_number=f"REG-PAGE-{i}",
                industry_type="Steel",
                latitude=10.0,
                longitude=20.0,
            )
            await factory_service.create_factory(cmd)

        query = ListFactoriesQuery(skip=2, limit=2)
        result = await factory_service.list_factories(query)

        assert len(result.items) == 2
        assert result.skip == 2
        assert result.limit == 2
        assert result.total == 5

    @pytest.mark.asyncio
    async def test_list_with_status_filter(self, factory_service):
        # Create 2 active + 1 suspended
        for i in range(2):
            cmd = CreateFactoryCommand(
                name=f"Active {i}",
                registration_number=f"REG-ACTIVE-{i}",
                industry_type="Steel",
                latitude=10.0,
                longitude=20.0,
            )
            await factory_service.create_factory(cmd)

        suspend_cmd = CreateFactoryCommand(
            name="Will Suspend",
            registration_number="REG-WILL-SUSPEND",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        created = await factory_service.create_factory(suspend_cmd)
        await factory_service.suspend_factory(SuspendFactoryCommand(
            factory_id=created.id,
            reason="Test",
            suspended_by=uuid4(),
        ))

        query = ListFactoriesQuery(status="ACTIVE")
        result = await factory_service.list_factories(query)

        assert result.total == 2
        assert all(f.status == "ACTIVE" for f in result.items)

    @pytest.mark.asyncio
    async def test_list_invalid_pagination_raises(self, factory_service):
        query = ListFactoriesQuery(skip=-1)
        with pytest.raises(ValueError):
            await factory_service.list_factories(query)


# =========================================================================
# get_factory
# =========================================================================
class TestGetFactory:
    @pytest.mark.asyncio
    async def test_get_factory_success(self, factory_service):
        cmd = CreateFactoryCommand(
            name="Get Me",
            registration_number="REG-GET",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        created = await factory_service.create_factory(cmd)

        dto = await factory_service.get_factory(created.id)
        assert dto.id == created.id
        assert dto.name == "Get Me"

    @pytest.mark.asyncio
    async def test_get_nonexistent_raises(self, factory_service):
        with pytest.raises(FactoryNotFoundError):
            await factory_service.get_factory(uuid4())


# =========================================================================
# delete_factory
# =========================================================================
class TestDeleteFactory:
    @pytest.mark.asyncio
    async def test_delete_factory_success(self, factory_service):
        cmd = CreateFactoryCommand(
            name="Delete Me",
            registration_number="REG-DEL",
            industry_type="Steel",
            latitude=10.0,
            longitude=20.0,
        )
        created = await factory_service.create_factory(cmd)

        result = await factory_service.delete_factory(created.id)
        assert result is True

        with pytest.raises(FactoryNotFoundError):
            await factory_service.get_factory(created.id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self, factory_service):
        with pytest.raises(FactoryNotFoundError):
            await factory_service.delete_factory(uuid4())
