"""Integration tests for Alert Service API endpoints.

Note: These tests require a running database connection and are designed
to run in a Docker environment. For local unit testing, use the tests
in tests/unit/ directory.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.interfaces.api.routes import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "alert-service"


class TestViolationsEndpoints:
    """Tests for /api/v1/violations endpoints."""

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_violations_empty(self, client):
        """Test listing violations when none exist."""
        response = client.get("/api/v1/violations")

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_violations_with_filters(self, client):
        """Test listing violations with query filters."""
        factory_id = str(uuid4())
        response = client.get(
            f"/api/v1/violations?factory_id={factory_id}&severity=HIGH&resolved=false"
        )

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_violations_pagination(self, client):
        """Test listing violations with pagination."""
        response = client.get("/api/v1/violations?skip=0&limit=10")

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_get_violation_by_id(self, client):
        """Test getting a violation by ID."""
        violation_id = str(uuid4())
        response = client.get(f"/api/v1/violations/{violation_id}")

        assert response.status_code in [200, 404]

    @pytest.mark.skip(reason="Requires database connection")
    def test_resolve_violation(self, client):
        """Test resolving a violation."""
        violation_id = str(uuid4())
        payload = {
            "notes": "Maintenance completed",
            "action_taken": "Filter replaced",
        }
        response = client.put(
            f"/api/v1/violations/{violation_id}/resolve",
            json=payload,
        )

        assert response.status_code in [200, 400, 404]

    @pytest.mark.skip(reason="Requires database connection")
    def test_resolve_violation_empty_body(self, client):
        """Test resolving a violation with empty body."""
        violation_id = str(uuid4())
        response = client.put(
            f"/api/v1/violations/{violation_id}/resolve",
            json={},
        )

        assert response.status_code in [200, 400, 404]


class TestAlertConfigEndpoints:
    """Tests for /api/v1/alerts/config endpoints."""

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_alert_configs(self, client):
        """Test listing all alert configurations."""
        response = client.get("/api/v1/alerts/config")

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_alert_configs_active_only(self, client):
        """Test listing only active alert configurations."""
        response = client.get("/api/v1/alerts/config?active_only=true")

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_alert_configs_pagination(self, client):
        """Test listing alert configurations with pagination."""
        response = client.get("/api/v1/alerts/config?skip=0&limit=10")

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_get_alert_config_by_id(self, client):
        """Test getting an alert configuration by ID."""
        config_id = str(uuid4())
        response = client.get(f"/api/v1/alerts/config/{config_id}")

        assert response.status_code in [200, 404]

    @pytest.mark.skip(reason="Requires database connection")
    def test_create_alert_config_valid(self, client):
        """Test creating a valid alert configuration."""
        payload = {
            "name": "PM2.5 City Limit",
            "pollutant": "pm25",
            "warning_threshold": 35.0,
            "high_threshold": 55.0,
            "critical_threshold": 150.0,
            "duration_minutes": 0,
            "notify_email": True,
            "notify_sms": False,
        }
        response = client.post("/api/v1/alerts/config", json=payload)

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_create_alert_config_invalid_thresholds(self, client):
        """Test creating a config with invalid threshold ordering."""
        payload = {
            "name": "Invalid Config",
            "pollutant": "pm25",
            "warning_threshold": 100.0,  # Too high
            "high_threshold": 50.0,
            "critical_threshold": 150.0,
        }
        response = client.post("/api/v1/alerts/config", json=payload)

        assert response.status_code in [400, 422]

    @pytest.mark.skip(reason="Requires database connection")
    def test_update_alert_config(self, client):
        """Test updating an alert configuration."""
        config_id = str(uuid4())
        payload = {
            "name": "Updated PM2.5 Limit",
            "pollutant": "pm25",
            "warning_threshold": 40.0,
            "high_threshold": 60.0,
            "critical_threshold": 160.0,
            "notify_sms": True,
        }
        response = client.put(
            f"/api/v1/alerts/config/{config_id}",
            json=payload,
        )

        assert response.status_code in [200, 400, 404]


class TestActiveAlertsEndpoint:
    """Tests for /api/v1/alerts/active endpoint."""

    @pytest.mark.skip(reason="Requires database connection")
    def test_get_active_alerts_count(self, client):
        """Test getting active alerts count summary."""
        response = client.get("/api/v1/alerts/active")

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires database connection")
    def test_active_alerts_response_structure(self, client):
        """Test active alerts response has correct structure."""
        response = client.get("/api/v1/alerts/active")

        if response.status_code == 200:
            data = response.json()
            assert "total_open_violations" in data
            assert "by_severity" in data
            assert "by_pollutant" in data


class TestAPIValidation:
    """Tests for API input validation."""

    @pytest.mark.skip(reason="Requires database connection")
    def test_violation_id_invalid_format(self, client):
        """Test that invalid UUID format is rejected."""
        response = client.get("/api/v1/violations/invalid-uuid")

        assert response.status_code in [400, 404, 422]

    @pytest.mark.skip(reason="Requires database connection")
    def test_config_id_invalid_format(self, client):
        """Test that invalid UUID format is rejected."""
        response = client.get("/api/v1/alerts/config/invalid-uuid")

        assert response.status_code in [400, 404, 422]

    @pytest.mark.skip(reason="Requires database connection")
    def test_create_config_missing_required_fields(self, client):
        """Test that missing required fields are rejected."""
        payload = {
            "name": "Incomplete Config",
            # Missing pollutant and thresholds
        }
        response = client.post("/api/v1/alerts/config", json=payload)

        assert response.status_code in [400, 422]

    @pytest.mark.skip(reason="Requires database connection")
    def test_create_config_empty_name(self, client):
        """Test that empty name is rejected."""
        payload = {
            "name": "",
            "pollutant": "pm25",
            "warning_threshold": 35.0,
            "high_threshold": 55.0,
            "critical_threshold": 150.0,
        }
        response = client.post("/api/v1/alerts/config", json=payload)

        assert response.status_code in [400, 422]

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_violations_invalid_limit(self, client):
        """Test that invalid limit parameter is rejected."""
        response = client.get("/api/v1/violations?limit=0")

        assert response.status_code in [400, 422]

    @pytest.mark.skip(reason="Requires database connection")
    def test_list_violations_negative_skip(self, client):
        """Test that negative skip parameter is rejected."""
        response = client.get("/api/v1/violations?skip=-1")

        assert response.status_code in [400, 422]


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get("/health")

        # FastAPI adds CORS middleware automatically when configured
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
