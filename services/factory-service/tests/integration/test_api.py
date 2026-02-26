"""Integration tests for the factory REST API.

Uses ``httpx.AsyncClient`` with a real FastAPI app backed by an
in-memory repository (no database required).
"""
from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.services.factory_application_service import (
    FactoryApplicationService,
)
from src.interfaces.api.routes import app
from src.interfaces.api.dependencies import get_factory_service
from tests.conftest import InMemoryFactoryRepository, MockEventPublisher


# =========================================================================
# Fixtures
# =========================================================================
@pytest.fixture
def _repo():
    return InMemoryFactoryRepository()


@pytest.fixture
def _publisher():
    return MockEventPublisher()


@pytest.fixture
def _service(_repo, _publisher):
    return FactoryApplicationService(
        factory_repository=_repo,
        event_publisher=_publisher,
    )


@pytest.fixture
async def client(_service):
    """HTTPX async client with overridden dependencies."""

    # Override the DI so we bypass DB + RabbitMQ.
    async def _override_factory_service():
        return _service

    # Override auth dependencies to return an admin user.
    from shared.auth.models import UserClaims
    from shared.auth.dependencies import get_current_user, require_role

    admin_user = UserClaims(user_id=uuid4(), role="admin")

    async def _override_current_user():
        return admin_user

    def _override_require_role(roles):
        async def _inner():
            return admin_user
        return _inner

    app.dependency_overrides[get_factory_service] = _override_factory_service
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[require_role] = _override_require_role

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


FACTORY_PAYLOAD = {
    "name": "Test Factory",
    "registration_number": "REG-API-001",
    "industry_type": "Steel",
    "latitude": 21.0285,
    "longitude": 105.8542,
    "emission_limits": {
        "pm25_limit": 50.0,
        "pm10_limit": 100.0,
    },
}


# =========================================================================
# Health
# =========================================================================
class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "factory-service"


# =========================================================================
# POST /factories
# =========================================================================
class TestCreateFactory:
    @pytest.mark.asyncio
    async def test_create_factory_201(self, client):
        resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        assert resp.status_code == 201

        data = resp.json()
        assert data["name"] == "Test Factory"
        assert data["registration_number"] == "REG-API-001"
        assert data["status"] == "ACTIVE"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_factory_duplicate_409(self, client):
        await client.post("/factories", json=FACTORY_PAYLOAD)
        resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_create_factory_invalid_payload_422(self, client):
        resp = await client.post("/factories", json={"name": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_factory_returns_emission_limits(self, client):
        resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        data = resp.json()
        assert "emission_limits" in data
        assert data["emission_limits"]["pm25_limit"] == 50.0


# =========================================================================
# GET /factories
# =========================================================================
class TestListFactories:
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        resp = await client.get("/factories")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_returns_created(self, client):
        await client.post("/factories", json=FACTORY_PAYLOAD)
        payload2 = FACTORY_PAYLOAD.copy()
        payload2["registration_number"] = "REG-API-002"
        payload2["name"] = "Second Factory"
        await client.post("/factories", json=payload2)

        resp = await client.get("/factories")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_pagination(self, client):
        for i in range(5):
            p = FACTORY_PAYLOAD.copy()
            p["registration_number"] = f"REG-PAGE-{i}"
            p["name"] = f"Factory {i}"
            await client.post("/factories", json=p)

        resp = await client.get("/factories", params={"skip": 2, "limit": 2})
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["skip"] == 2
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_list_filter_by_status(self, client):
        # Create and suspend one
        resp1 = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = resp1.json()["id"]
        await client.post(
            f"/factories/{factory_id}/suspend",
            json={"reason": "Test", "suspended_by": str(uuid4())},
        )

        # Create another (stays active)
        p2 = FACTORY_PAYLOAD.copy()
        p2["registration_number"] = "REG-ACTIVE-FILTER"
        await client.post("/factories", json=p2)

        resp = await client.get("/factories", params={"status": "ACTIVE"})
        data = resp.json()
        assert data["total"] == 1
        assert all(f["status"] == "ACTIVE" for f in data["items"])


# =========================================================================
# GET /factories/{id}
# =========================================================================
class TestGetFactory:
    @pytest.mark.asyncio
    async def test_get_factory_200(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        resp = await client.get(f"/factories/{factory_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == factory_id
        assert data["name"] == "Test Factory"

    @pytest.mark.asyncio
    async def test_get_factory_not_found_404(self, client):
        fake_id = str(uuid4())
        resp = await client.get(f"/factories/{fake_id}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# =========================================================================
# PUT /factories/{id}
# =========================================================================
class TestUpdateFactory:
    @pytest.mark.asyncio
    async def test_update_factory_200(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        resp = await client.put(
            f"/factories/{factory_id}",
            json={"name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_not_found_404(self, client):
        resp = await client.put(
            f"/factories/{uuid4()}",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404


# =========================================================================
# POST /factories/{id}/suspend
# =========================================================================
class TestSuspendFactory:
    @pytest.mark.asyncio
    async def test_suspend_factory_200(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        resp = await client.post(
            f"/factories/{factory_id}/suspend",
            json={
                "reason": "Emission violation",
                "suspended_by": str(uuid4()),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "SUSPENDED"

    @pytest.mark.asyncio
    async def test_suspend_not_found_404(self, client):
        resp = await client.post(
            f"/factories/{uuid4()}/suspend",
            json={"reason": "Test", "suspended_by": str(uuid4())},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_suspend_already_suspended_400(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        # First suspend
        await client.post(
            f"/factories/{factory_id}/suspend",
            json={"reason": "First", "suspended_by": str(uuid4())},
        )
        # Second suspend
        resp = await client.post(
            f"/factories/{factory_id}/suspend",
            json={"reason": "Second", "suspended_by": str(uuid4())},
        )
        assert resp.status_code == 400


# =========================================================================
# POST /factories/{id}/resume
# =========================================================================
class TestResumeFactory:
    @pytest.mark.asyncio
    async def test_resume_factory_200(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        # Suspend first
        await client.post(
            f"/factories/{factory_id}/suspend",
            json={"reason": "Test", "suspended_by": str(uuid4())},
        )

        # Resume
        resp = await client.post(
            f"/factories/{factory_id}/resume",
            json={"resumed_by": str(uuid4()), "notes": "Fixed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_resume_not_suspended_400(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        resp = await client.post(
            f"/factories/{factory_id}/resume",
            json={"resumed_by": str(uuid4())},
        )
        assert resp.status_code == 400


# =========================================================================
# DELETE /factories/{id}
# =========================================================================
class TestDeleteFactory:
    @pytest.mark.asyncio
    async def test_delete_factory_200(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        resp = await client.delete(f"/factories/{factory_id}")
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

        # Confirm it's gone
        get_resp = await client.get(f"/factories/{factory_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found_404(self, client):
        resp = await client.delete(f"/factories/{uuid4()}")
        assert resp.status_code == 404


# =========================================================================
# GET /factories/{id}/emissions
# =========================================================================
class TestGetEmissions:
    @pytest.mark.asyncio
    async def test_get_emissions_200(self, client):
        create_resp = await client.post("/factories", json=FACTORY_PAYLOAD)
        factory_id = create_resp.json()["id"]

        resp = await client.get(f"/factories/{factory_id}/emissions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["factory_id"] == factory_id
        assert data["factory_name"] == "Test Factory"
        assert "emission_limits" in data

    @pytest.mark.asyncio
    async def test_get_emissions_not_found_404(self, client):
        resp = await client.get(f"/factories/{uuid4()}/emissions")
        assert resp.status_code == 404
