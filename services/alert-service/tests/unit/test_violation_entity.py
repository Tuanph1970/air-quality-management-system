"""Unit tests for Violation entity."""
import pytest
from uuid import uuid4

from src.domain.entities.violation import Violation
from src.domain.value_objects.severity import Severity
from src.domain.exceptions.alert_exceptions import ViolationAlreadyResolvedError
from src.domain.events.alert_events import ViolationDetected, ViolationResolved


class TestViolationCreate:
    """Tests for Violation.create() factory method."""

    def test_create_violation_success(self, sample_violation_data):
        """Test creating a violation with valid data."""
        violation = Violation.create(**sample_violation_data)

        assert violation.id is not None
        assert violation.factory_id == sample_violation_data["factory_id"]
        assert violation.sensor_id == sample_violation_data["sensor_id"]
        assert violation.pollutant == sample_violation_data["pollutant"]
        assert violation.measured_value == sample_violation_data["measured_value"]
        assert violation.permitted_value == sample_violation_data["permitted_value"]
        assert violation.status == "OPEN"
        assert violation.is_open is True
        assert violation.is_resolved is False

    def test_create_violation_calculates_exceedance(self):
        """Test exceedance percentage calculation."""
        violation = Violation.create(
            factory_id=uuid4(),
            sensor_id=uuid4(),
            pollutant="pm25",
            measured_value=75.0,  # 50% over 50
            permitted_value=50.0,
            severity=Severity.WARNING,
        )

        assert violation.exceedance_percentage == 50.0

    def test_create_violation_emits_event(self, sample_violation_data):
        """Test that creating a violation emits ViolationDetected event."""
        violation = Violation.create(**sample_violation_data)
        events = violation.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], ViolationDetected)
        assert events[0].violation_id == violation.id
        assert events[0].factory_id == violation.factory_id
        assert events[0].pollutant == violation.pollutant
        assert events[0].severity == Severity.WARNING.value

    def test_create_violation_negative_measured_value_raises(self, sample_violation_data):
        """Test that negative measured value raises ValueError."""
        sample_violation_data["measured_value"] = -10.0

        with pytest.raises(ValueError, match="non-negative"):
            Violation.create(**sample_violation_data)

    def test_create_violation_zero_permitted_value_raises(self, sample_violation_data):
        """Test that zero permitted value raises ValueError."""
        sample_violation_data["permitted_value"] = 0.0

        with pytest.raises(ValueError, match="positive"):
            Violation.create(**sample_violation_data)


class TestViolationResolve:
    """Tests for Violation.resolve() method."""

    def test_resolve_open_violation_success(self, sample_violation):
        """Test resolving an open violation."""
        sample_violation.resolve(
            notes="Filter replaced",
            action_taken="Maintenance performed",
        )

        assert sample_violation.status == "RESOLVED"
        assert sample_violation.is_resolved is True
        assert sample_violation.resolved_at is not None
        assert sample_violation.notes == "Filter replaced"
        assert sample_violation.action_taken == "Maintenance performed"

    def test_resolve_violation_emits_event(self, sample_violation):
        """Test that resolving emits ViolationResolved event."""
        sample_violation.resolve(notes="Test resolution")
        events = sample_violation.collect_events()

        # First event is ViolationDetected from create, second is ViolationResolved
        resolved_events = [e for e in events if isinstance(e, ViolationResolved)]
        assert len(resolved_events) == 1
        assert resolved_events[0].violation_id == sample_violation.id

    def test_resolve_already_resolved_raises(self, sample_violation):
        """Test that resolving an already resolved violation raises."""
        sample_violation.resolve()

        with pytest.raises(ViolationAlreadyResolvedError):
            sample_violation.resolve()

    def test_resolve_critical_violation(self):
        """Test resolving a CRITICAL severity violation."""
        violation = Violation.create(
            factory_id=uuid4(),
            sensor_id=uuid4(),
            pollutant="co",
            measured_value=50.0,
            permitted_value=10.0,
            severity=Severity.CRITICAL,
        )

        violation.resolve(action_taken="Emergency shutdown")
        assert violation.is_resolved is True
        assert violation.is_critical is True


class TestViolationProperties:
    """Tests for Violation query properties."""

    def test_is_open_true(self, sample_violation):
        """Test is_open property for open violation."""
        assert sample_violation.is_open is True

    def test_is_open_false_after_resolve(self, sample_violation):
        """Test is_open property after resolution."""
        sample_violation.resolve()
        assert sample_violation.is_open is False

    def test_is_resolved_false(self, sample_violation):
        """Test is_resolved property for open violation."""
        assert sample_violation.is_resolved is False

    def test_is_resolved_true_after_resolve(self, sample_violation):
        """Test is_resolved property after resolution."""
        sample_violation.resolve()
        assert sample_violation.is_resolved is True

    def test_is_critical_for_warning_severity(self, sample_violation):
        """Test is_critical for WARNING severity."""
        assert sample_violation.is_critical is False

    def test_is_critical_for_critical_severity(self):
        """Test is_critical for CRITICAL severity."""
        violation = Violation.create(
            factory_id=uuid4(),
            sensor_id=uuid4(),
            pollutant="pm25",
            measured_value=200.0,
            permitted_value=50.0,
            severity=Severity.CRITICAL,
        )
        assert violation.is_critical is True


class TestViolationCollectEvents:
    """Tests for Violation.collect_events() method."""

    def test_collect_events_clears_list(self, sample_violation):
        """Test that collect_events clears the internal list."""
        events = sample_violation.collect_events()
        assert len(events) == 1

        # Second call should return empty list
        events2 = sample_violation.collect_events()
        assert len(events2) == 0

    def test_collect_events_multiple_events(self):
        """Test collecting events after multiple operations."""
        violation = Violation.create(
            factory_id=uuid4(),
            sensor_id=uuid4(),
            pollutant="pm25",
            measured_value=85.0,
            permitted_value=50.0,
            severity=Severity.HIGH,
        )

        # One event from creation
        events = violation.collect_events()
        assert len(events) == 1

        # Resolve and collect again
        violation.resolve()
        events = violation.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ViolationResolved)
