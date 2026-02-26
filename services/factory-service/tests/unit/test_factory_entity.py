"""Unit tests for the Factory domain entity."""
from __future__ import annotations

from uuid import uuid4

import pytest

from src.domain.entities.factory import Factory
from src.domain.exceptions.factory_exceptions import (
    FactoryAlreadySuspendedError,
    FactoryClosedError,
    FactoryNotSuspendedError,
)
from src.domain.value_objects.factory_status import FactoryStatus


# =========================================================================
# Factory.create()
# =========================================================================
class TestFactoryCreate:
    def test_create_sets_fields(self, sample_factory_data):
        factory = Factory.create(**sample_factory_data)

        assert factory.name == "Viet Steel Manufacturing"
        assert factory.registration_number == "REG-2024-001"
        assert factory.industry_type == "Steel"
        assert factory.location.latitude == 21.0285
        assert factory.location.longitude == 105.8542

    def test_create_sets_active_status(self, sample_factory_data):
        factory = Factory.create(**sample_factory_data)
        assert factory.status == FactoryStatus.ACTIVE

    def test_create_generates_uuid(self, sample_factory_data):
        factory = Factory.create(**sample_factory_data)
        assert factory.id is not None

    def test_create_sets_timestamps(self, sample_factory_data):
        factory = Factory.create(**sample_factory_data)
        assert factory.created_at is not None
        assert factory.updated_at is not None

    def test_create_emits_factory_created_event(self, sample_factory_data):
        factory = Factory.create(**sample_factory_data)
        events = factory.collect_events()

        assert len(events) == 1
        assert events[0].event_type == "factory.created"
        assert events[0].factory_id == factory.id
        assert events[0].name == "Viet Steel Manufacturing"

    def test_create_with_empty_emission_limits(self):
        factory = Factory.create(
            name="Test",
            registration_number="REG-001",
            industry_type="Test",
            latitude=10.0,
            longitude=20.0,
            emission_limits={},
        )
        assert factory.emission_limits.pm25_limit == 0.0

    def test_two_factories_have_different_ids(self, sample_factory_data):
        f1 = Factory.create(**sample_factory_data)
        data2 = sample_factory_data.copy()
        data2["registration_number"] = "REG-2024-002"
        f2 = Factory.create(**data2)
        assert f1.id != f2.id


# =========================================================================
# Factory.suspend()
# =========================================================================
class TestFactorySuspend:
    def test_suspend_active_factory(self, sample_factory):
        user_id = uuid4()
        sample_factory.suspend(reason="Emission violation", suspended_by=user_id)

        assert sample_factory.status == FactoryStatus.SUSPENDED

    def test_suspend_emits_two_events(self, sample_factory):
        sample_factory.suspend(reason="Violation", suspended_by=uuid4())
        events = sample_factory.collect_events()

        # create event + status changed + suspended = 3
        # But collect_events was already called in fixture? No, fixture
        # returns a fresh factory with events not yet collected.
        event_types = [e.event_type for e in events]
        assert "factory.created" in event_types
        assert "factory.status.changed" in event_types
        assert "factory.suspended" in event_types

    def test_suspend_already_suspended_raises(self, sample_factory):
        sample_factory.suspend(reason="First", suspended_by=uuid4())
        with pytest.raises(FactoryAlreadySuspendedError):
            sample_factory.suspend(reason="Second", suspended_by=uuid4())

    def test_suspend_closed_factory_raises(self, sample_factory):
        sample_factory.close(reason="Shutdown")
        with pytest.raises(FactoryClosedError):
            sample_factory.suspend(reason="Try", suspended_by=uuid4())

    def test_suspend_warning_factory(self, sample_factory):
        sample_factory.status = FactoryStatus.WARNING
        sample_factory.suspend(reason="Violation", suspended_by=uuid4())
        assert sample_factory.status == FactoryStatus.SUSPENDED

    def test_suspend_updates_timestamp(self, sample_factory):
        old_ts = sample_factory.updated_at
        sample_factory.suspend(reason="Test", suspended_by=uuid4())
        assert sample_factory.updated_at >= old_ts


# =========================================================================
# Factory.resume()
# =========================================================================
class TestFactoryResume:
    def test_resume_suspended_factory(self, sample_factory):
        sample_factory.suspend(reason="Violation", suspended_by=uuid4())
        sample_factory.resume(resumed_by=uuid4(), notes="Fixed")

        assert sample_factory.status == FactoryStatus.ACTIVE

    def test_resume_not_suspended_raises(self, sample_factory):
        with pytest.raises(FactoryNotSuspendedError):
            sample_factory.resume(resumed_by=uuid4())

    def test_resume_emits_events(self, sample_factory):
        sample_factory.suspend(reason="Test", suspended_by=uuid4())
        sample_factory.collect_events()  # clear previous events

        sample_factory.resume(resumed_by=uuid4(), notes="OK")
        events = sample_factory.collect_events()

        event_types = [e.event_type for e in events]
        assert "factory.status.changed" in event_types
        assert "factory.resumed" in event_types

    def test_resume_updates_timestamp(self, sample_factory):
        sample_factory.suspend(reason="Test", suspended_by=uuid4())
        old_ts = sample_factory.updated_at
        sample_factory.resume(resumed_by=uuid4())
        assert sample_factory.updated_at >= old_ts


# =========================================================================
# Factory.update_status_from_emissions()
# =========================================================================
class TestUpdateStatusFromEmissions:
    def test_high_aqi_sets_critical(self, sample_factory):
        sample_factory.update_status_from_emissions(current_aqi=250)
        assert sample_factory.status == FactoryStatus.CRITICAL

    def test_medium_aqi_sets_warning(self, sample_factory):
        sample_factory.update_status_from_emissions(current_aqi=160)
        assert sample_factory.status == FactoryStatus.WARNING

    def test_low_aqi_stays_active(self, sample_factory):
        sample_factory.update_status_from_emissions(current_aqi=100)
        assert sample_factory.status == FactoryStatus.ACTIVE

    def test_boundary_200_is_warning(self, sample_factory):
        sample_factory.update_status_from_emissions(current_aqi=200)
        assert sample_factory.status == FactoryStatus.WARNING

    def test_boundary_150_is_active(self, sample_factory):
        sample_factory.update_status_from_emissions(current_aqi=150)
        assert sample_factory.status == FactoryStatus.ACTIVE

    def test_boundary_201_is_critical(self, sample_factory):
        sample_factory.update_status_from_emissions(current_aqi=201)
        assert sample_factory.status == FactoryStatus.CRITICAL

    def test_skips_suspended_factory(self, sample_factory):
        sample_factory.suspend(reason="Test", suspended_by=uuid4())
        sample_factory.update_status_from_emissions(current_aqi=250)
        assert sample_factory.status == FactoryStatus.SUSPENDED

    def test_skips_closed_factory(self, sample_factory):
        sample_factory.close(reason="Done")
        sample_factory.update_status_from_emissions(current_aqi=250)
        assert sample_factory.status == FactoryStatus.CLOSED

    def test_emits_status_changed_event(self, sample_factory):
        sample_factory.collect_events()  # clear create event
        sample_factory.update_status_from_emissions(current_aqi=250)
        events = sample_factory.collect_events()

        assert len(events) == 1
        assert events[0].event_type == "factory.status.changed"
        assert events[0].old_status == "ACTIVE"
        assert events[0].new_status == "CRITICAL"

    def test_no_event_when_status_unchanged(self, sample_factory):
        sample_factory.collect_events()
        sample_factory.update_status_from_emissions(current_aqi=100)  # stays ACTIVE
        events = sample_factory.collect_events()
        assert len(events) == 0


# =========================================================================
# Event collection
# =========================================================================
class TestEventCollection:
    def test_collect_returns_events(self, sample_factory):
        events = sample_factory.collect_events()
        assert len(events) >= 1

    def test_collect_clears_events(self, sample_factory):
        sample_factory.collect_events()
        events = sample_factory.collect_events()
        assert len(events) == 0

    def test_events_accumulate(self, sample_factory):
        sample_factory.update_status_from_emissions(current_aqi=250)
        sample_factory.update_status_from_emissions(current_aqi=100)
        events = sample_factory.collect_events()
        # create + critical + back to active = 3
        assert len(events) == 3

    def test_collect_returns_copy(self, sample_factory):
        events = sample_factory.collect_events()
        assert isinstance(events, list)
        # Modifying returned list doesn't affect internal state
        events.append("spurious")
        assert len(sample_factory.collect_events()) == 0


# =========================================================================
# Factory.update()
# =========================================================================
class TestFactoryUpdate:
    def test_update_name(self, sample_factory):
        sample_factory.collect_events()
        sample_factory.update(name="New Name")

        assert sample_factory.name == "New Name"
        events = sample_factory.collect_events()
        assert any(e.event_type == "factory.updated" for e in events)

    def test_update_closed_raises(self, sample_factory):
        sample_factory.close()
        with pytest.raises(FactoryClosedError):
            sample_factory.update(name="Fail")

    def test_update_no_fields_no_event(self, sample_factory):
        sample_factory.collect_events()
        sample_factory.update()
        assert len(sample_factory.collect_events()) == 0


# =========================================================================
# Factory.close()
# =========================================================================
class TestFactoryClose:
    def test_close_sets_closed_status(self, sample_factory):
        sample_factory.close(reason="Permanent shutdown")
        assert sample_factory.status == FactoryStatus.CLOSED

    def test_close_already_closed_raises(self, sample_factory):
        sample_factory.close()
        with pytest.raises(FactoryClosedError):
            sample_factory.close()

    def test_close_emits_status_changed(self, sample_factory):
        sample_factory.collect_events()
        sample_factory.close(reason="Done")
        events = sample_factory.collect_events()
        assert any(e.event_type == "factory.status.changed" for e in events)
