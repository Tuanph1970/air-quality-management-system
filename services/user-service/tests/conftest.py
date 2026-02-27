"""Shared test fixtures for the user service test suite.

Bootstraps ``shared.*`` modules with lightweight stubs so tests can run
locally without Docker.
"""
from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4

import pytest


# =========================================================================
# 1. Bootstrap shared modules
# =========================================================================

# --- shared.events.base_event ---
_shared_events_base = types.ModuleType("shared.events.base_event")


@dataclass
class _DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


_shared_events_base.DomainEvent = _DomainEvent

# --- shared.events.user_events ---
_shared_events_user = types.ModuleType("shared.events.user_events")


@dataclass
class _UserRegistered(_DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    email: str = ""
    role: str = "PUBLIC"
    event_type: str = "user.registered"


@dataclass
class _UserPasswordChanged(_DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = "user.password.changed"


@dataclass
class _UserLoggedIn(_DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    email: str = ""
    logged_in_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = "user.logged_in"


_shared_events_user.UserRegistered = _UserRegistered
_shared_events_user.UserPasswordChanged = _UserPasswordChanged
_shared_events_user.UserLoggedIn = _UserLoggedIn

# Wire into sys.modules
_shared = types.ModuleType("shared")
_shared_events = types.ModuleType("shared.events")
sys.modules.setdefault("shared", _shared)
sys.modules.setdefault("shared.events", _shared_events)
sys.modules.setdefault("shared.events.base_event", _shared_events_base)
sys.modules.setdefault("shared.events.user_events", _shared_events_user)


# =========================================================================
# 2. Test fixtures
# =========================================================================

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "role": "PUBLIC",
    }


@pytest.fixture
def sample_email() -> str:
    """Sample email for testing."""
    return "test@example.com"


@pytest.fixture
def sample_password() -> str:
    """Sample password for testing."""
    return "SecurePass123!"


@pytest.fixture
def anyio_backend():
    return "asyncio"
