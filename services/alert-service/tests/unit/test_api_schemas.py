"""Unit tests for API schemas."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from pydantic import ValidationError

from src.interfaces.api.schemas import (
    ViolationResponse,
    ViolationListResponse,
    ResolveViolationRequest,
    AlertConfigRequest,
    AlertConfigResponse,
    AlertConfigListResponse,
    ActiveAlertsSummary,
)


class TestViolationResponse:
    """Tests for ViolationResponse schema."""

    def test_violation_response_valid(self):
        """Test creating a valid ViolationResponse."""
        data = {
            "id": uuid4(),
            "factory_id": uuid4(),
            "sensor_id": uuid4(),
            "pollutant": "pm25",
            "measured_value": 85.5,
            "permitted_value": 50.0,
            "exceedance_percentage": 71.0,
            "severity": "HIGH",
            "status": "OPEN",
            "detected_at": datetime.now(timezone.utc),
        }

        response = ViolationResponse(**data)

        assert response.id == data["id"]
        assert response.pollutant == "pm25"
        assert response.severity == "HIGH"
        assert response.status == "OPEN"

    def test_violation_response_optional_fields(self):
        """Test ViolationResponse with optional fields."""
        data = {
            "id": uuid4(),
            "factory_id": uuid4(),
            "sensor_id": uuid4(),
            "pollutant": "co",
            "measured_value": 15.0,
            "permitted_value": 10.0,
            "exceedance_percentage": 50.0,
            "severity": "WARNING",
            "status": "RESOLVED",
            "detected_at": datetime.now(timezone.utc),
            "resolved_at": datetime.now(timezone.utc),
            "action_taken": "Maintenance",
            "notes": "Filter cleaned",
        }

        response = ViolationResponse(**data)

        assert response.resolved_at is not None
        assert response.action_taken == "Maintenance"
        assert response.notes == "Filter cleaned"

    def test_violation_response_from_attributes(self):
        """Test ViolationResponse with from_attributes mode."""
        # Simulate an ORM object
        class MockViolation:
            id = uuid4()
            factory_id = uuid4()
            sensor_id = uuid4()
            pollutant = "pm25"
            measured_value = 100.0
            permitted_value = 50.0
            exceedance_percentage = 100.0
            severity = "CRITICAL"
            status = "OPEN"
            detected_at = datetime.now(timezone.utc)
            resolved_at = None
            action_taken = ""
            notes = ""

        mock = MockViolation()
        response = ViolationResponse.model_validate(mock)

        assert response.pollutant == "pm25"
        assert response.severity == "CRITICAL"


class TestViolationListResponse:
    """Tests for ViolationListResponse schema."""

    def test_violation_list_response_valid(self):
        """Test creating a valid ViolationListResponse."""
        violations = [
            ViolationResponse(
                id=uuid4(),
                factory_id=uuid4(),
                sensor_id=uuid4(),
                pollutant="pm25",
                measured_value=85.0,
                permitted_value=50.0,
                exceedance_percentage=70.0,
                severity="HIGH",
                status="OPEN",
                detected_at=datetime.now(timezone.utc),
            )
        ]

        response = ViolationListResponse(data=violations, total=1)

        assert response.total == 1
        assert len(response.data) == 1

    def test_violation_list_response_empty(self):
        """Test ViolationListResponse with empty list."""
        response = ViolationListResponse(data=[], total=0)

        assert response.total == 0
        assert len(response.data) == 0


class TestResolveViolationRequest:
    """Tests for ResolveViolationRequest schema."""

    def test_resolve_request_minimal(self):
        """Test ResolveViolationRequest with minimal data."""
        request = ResolveViolationRequest()

        assert request.notes == ""
        assert request.action_taken == ""

    def test_resolve_request_with_data(self):
        """Test ResolveViolationRequest with resolution data."""
        request = ResolveViolationRequest(
            notes="Filter replaced",
            action_taken="Scheduled maintenance",
        )

        assert request.notes == "Filter replaced"
        assert request.action_taken == "Scheduled maintenance"


class TestAlertConfigRequest:
    """Tests for AlertConfigRequest schema."""

    def test_alert_config_request_valid(self):
        """Test creating a valid AlertConfigRequest."""
        data = {
            "name": "PM2.5 City Limit",
            "pollutant": "pm25",
            "warning_threshold": 35.0,
            "high_threshold": 55.0,
            "critical_threshold": 150.0,
        }

        request = AlertConfigRequest(**data)

        assert request.name == "PM2.5 City Limit"
        assert request.pollutant == "pm25"
        assert request.notify_email is True
        assert request.notify_sms is False

    def test_alert_config_request_threshold_validation(self):
        """Test that thresholds must be ordered correctly."""
        data = {
            "name": "Invalid Config",
            "pollutant": "pm25",
            "warning_threshold": 100.0,  # Too high
            "high_threshold": 50.0,
            "critical_threshold": 150.0,
        }

        with pytest.raises(ValidationError, match="threshold"):
            AlertConfigRequest(**data)

    def test_alert_config_request_positive_thresholds(self):
        """Test that thresholds must be positive."""
        data = {
            "name": "Config",
            "pollutant": "pm25",
            "warning_threshold": -10.0,
            "high_threshold": 50.0,
            "critical_threshold": 150.0,
        }

        with pytest.raises(ValidationError):
            AlertConfigRequest(**data)

    def test_alert_config_request_name_length(self):
        """Test name length validation."""
        data = {
            "name": "",  # Empty name
            "pollutant": "pm25",
            "warning_threshold": 35.0,
            "high_threshold": 55.0,
            "critical_threshold": 150.0,
        }

        with pytest.raises(ValidationError):
            AlertConfigRequest(**data)

    def test_alert_config_request_name_too_long(self):
        """Test name max length validation."""
        data = {
            "name": "A" * 101,  # Exceeds 100 chars
            "pollutant": "pm25",
            "warning_threshold": 35.0,
            "high_threshold": 55.0,
            "critical_threshold": 150.0,
        }

        with pytest.raises(ValidationError):
            AlertConfigRequest(**data)

    def test_alert_config_request_duration_validation(self):
        """Test duration_minutes must be non-negative."""
        data = {
            "name": "Config",
            "pollutant": "pm25",
            "warning_threshold": 35.0,
            "high_threshold": 55.0,
            "critical_threshold": 150.0,
            "duration_minutes": -10,
        }

        with pytest.raises(ValidationError):
            AlertConfigRequest(**data)


class TestAlertConfigResponse:
    """Tests for AlertConfigResponse schema."""

    def test_alert_config_response_valid(self):
        """Test creating a valid AlertConfigResponse."""
        data = {
            "id": uuid4(),
            "name": "PM2.5 Limit",
            "pollutant": "pm25",
            "warning_threshold": 35.0,
            "high_threshold": 55.0,
            "critical_threshold": 150.0,
            "duration_minutes": 0,
            "is_active": True,
            "notify_email": True,
            "notify_sms": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        response = AlertConfigResponse(**data)

        assert response.name == "PM2.5 Limit"
        assert response.is_active is True

    def test_alert_config_response_from_attributes(self):
        """Test AlertConfigResponse with from_attributes mode."""
        class MockConfig:
            id = uuid4()
            name = "CO Limit"
            pollutant = "co"
            warning_threshold = 5.0
            high_threshold = 10.0
            critical_threshold = 30.0
            duration_minutes = 15
            is_active = True
            notify_email = False
            notify_sms = True
            created_at = datetime.now(timezone.utc)
            updated_at = datetime.now(timezone.utc)

        mock = MockConfig()
        response = AlertConfigResponse.model_validate(mock)

        assert response.pollutant == "co"
        assert response.notify_sms is True


class TestAlertConfigListResponse:
    """Tests for AlertConfigListResponse schema."""

    def test_alert_config_list_response_valid(self):
        """Test creating a valid AlertConfigListResponse."""
        configs = [
            AlertConfigResponse(
                id=uuid4(),
                name="PM2.5 Limit",
                pollutant="pm25",
                warning_threshold=35.0,
                high_threshold=55.0,
                critical_threshold=150.0,
                duration_minutes=0,
                is_active=True,
                notify_email=True,
                notify_sms=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]

        response = AlertConfigListResponse(data=configs, total=1)

        assert response.total == 1
        assert len(response.data) == 1


class TestActiveAlertsSummary:
    """Tests for ActiveAlertsSummary schema."""

    def test_active_alerts_summary_default(self):
        """Test ActiveAlertsSummary with default values."""
        summary = ActiveAlertsSummary(total_open_violations=0)

        assert summary.total_open_violations == 0
        assert summary.by_severity["WARNING"] == 0
        assert summary.by_severity["HIGH"] == 0
        assert summary.by_severity["CRITICAL"] == 0
        assert summary.by_pollutant == {}

    def test_active_alerts_summary_with_data(self):
        """Test ActiveAlertsSummary with data."""
        summary = ActiveAlertsSummary(
            total_open_violations=10,
            by_severity={"WARNING": 5, "HIGH": 3, "CRITICAL": 2},
            by_pollutant={"pm25": 4, "co": 3, "no2": 3},
        )

        assert summary.total_open_violations == 10
        assert summary.by_severity["WARNING"] == 5
        assert summary.by_pollutant["pm25"] == 4
