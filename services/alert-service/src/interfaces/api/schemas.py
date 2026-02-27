"""Pydantic request/response schemas for the Alert Service API."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Violation Schemas
# =============================================================================


class ViolationResponse(BaseModel):
    """Response schema for a single violation."""

    id: UUID
    factory_id: UUID
    sensor_id: UUID
    pollutant: str
    measured_value: float
    permitted_value: float
    exceedance_percentage: float
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    action_taken: str = ""
    notes: str = ""

    model_config = {"from_attributes": True}


class ViolationListResponse(BaseModel):
    """Response schema for a list of violations with pagination."""

    data: List[ViolationResponse]
    total: int


class ResolveViolationRequest(BaseModel):
    """Request schema to resolve a violation."""

    notes: str = ""
    action_taken: str = ""


# =============================================================================
# Alert Configuration Schemas
# =============================================================================


class AlertConfigRequest(BaseModel):
    """Request schema to create/update an alert configuration."""

    name: str = Field(..., min_length=1, max_length=100)
    pollutant: str = Field(..., min_length=1, max_length=20)
    warning_threshold: float = Field(..., gt=0)
    high_threshold: float = Field(..., gt=0)
    critical_threshold: float = Field(..., gt=0)
    duration_minutes: int = Field(default=0, ge=0)
    notify_email: bool = True
    notify_sms: bool = False

    def model_post_init(self, __context) -> None:
        """Validate threshold ordering after initialization."""
        if not (self.warning_threshold < self.high_threshold < self.critical_threshold):
            raise ValueError(
                "Thresholds must be ordered: warning < high < critical"
            )


class AlertConfigResponse(BaseModel):
    """Response schema for an alert configuration."""

    id: UUID
    name: str
    pollutant: str
    warning_threshold: float
    high_threshold: float
    critical_threshold: float
    duration_minutes: int
    is_active: bool
    notify_email: bool
    notify_sms: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertConfigListResponse(BaseModel):
    """Response schema for a list of alert configurations."""

    data: List[AlertConfigResponse]
    total: int


# =============================================================================
# Summary / Dashboard Schemas
# =============================================================================


class ActiveAlertsSummary(BaseModel):
    """Summary response for active alerts count."""

    total_open_violations: int
    by_severity: dict[str, int] = Field(
        default_factory=lambda: {"WARNING": 0, "HIGH": 0, "CRITICAL": 0}
    )
    by_pollutant: dict[str, int] = Field(default_factory=dict)
