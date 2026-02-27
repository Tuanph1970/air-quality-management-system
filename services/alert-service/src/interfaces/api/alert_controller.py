"""Alert Controller — HTTP request handlers for the Alert Service.

This module contains the FastAPI route handlers (controllers) that:
1. Receive HTTP requests
2. Parse and validate input via Pydantic schemas
3. Delegate to application services
4. Return HTTP responses

All business logic is delegated to the application layer.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...application.dto.alert_dto import ViolationDTO
from ...application.dto.alert_config_dto import AlertConfigDTO
from ...application.services.alert_application_service import (
    AlertApplicationService,
    get_alert_application_service,
)
from .schemas import (
    ActiveAlertsSummary,
    AlertConfigListResponse,
    AlertConfigRequest,
    AlertConfigResponse,
    ResolveViolationRequest,
    ViolationListResponse,
    ViolationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["alerts"])


# =============================================================================
# Dependency Injection
# =============================================================================


def get_service() -> AlertApplicationService:
    """Inject the alert application service."""
    return next(get_alert_application_service())


# =============================================================================
# Violation Endpoints
# =============================================================================


@router.get("/violations", response_model=ViolationListResponse)
async def list_violations(
    factory_id: Optional[UUID] = Query(
        None, description="Filter by factory ID"
    ),
    severity: Optional[str] = Query(
        None, description="Filter by severity (WARNING, HIGH, CRITICAL)"
    ),
    resolved: Optional[bool] = Query(
        None, description="Filter by resolved status (true=RESOLVED, false=OPEN)"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    service: AlertApplicationService = Depends(get_service),
) -> ViolationListResponse:
    """List violations with optional filters.

    - **factory_id**: Filter violations by factory
    - **severity**: Filter by severity level
    - **resolved**: Filter by resolution status
    - **skip/limit**: Pagination
    """
    status_filter = None
    if resolved is not None:
        status_filter = "RESOLVED" if resolved else "OPEN"

    if factory_id:
        violations = await service.get_violations_by_factory(
            factory_id=factory_id,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
    elif severity:
        violations = await service.get_violations_by_severity(
            severity=severity.upper(),
            skip=skip,
            limit=limit,
        )
    elif status_filter:
        if status_filter == "OPEN":
            violations = await service.get_active_violations(skip=skip, limit=limit)
        else:
            violations = await service.get_resolved_violations(skip=skip, limit=limit)
    else:
        violations = await service.get_all_violations(skip=skip, limit=limit)

    total = await service.count_violations(
        factory_id=factory_id, status=status_filter
    )

    return ViolationListResponse(
        data=[ViolationResponse.model_validate(v) for v in violations],
        total=total,
    )


@router.get("/violations/{violation_id}", response_model=ViolationResponse)
async def get_violation(
    violation_id: UUID,
    service: AlertApplicationService = Depends(get_service),
) -> ViolationResponse:
    """Get details of a specific violation."""
    violation = await service.get_violation_by_id(violation_id)
    if violation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Violation {violation_id} not found",
        )
    return ViolationResponse.model_validate(violation)


@router.put(
    "/violations/{violation_id}/resolve", response_model=ViolationResponse
)
async def resolve_violation(
    violation_id: UUID,
    request: ResolveViolationRequest,
    service: AlertApplicationService = Depends(get_service),
) -> ViolationResponse:
    """Resolve an open violation.

    - **notes**: Optional notes about the resolution
    - **action_taken**: Description of corrective action taken
    """
    try:
        violation = await service.resolve_violation_by_id(
            violation_id=violation_id,
            notes=request.notes,
            action_taken=request.action_taken,
        )
        return ViolationResponse.model_validate(violation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


# =============================================================================
# Alert Configuration Endpoints
# =============================================================================


@router.get("/alerts/config", response_model=AlertConfigListResponse)
async def list_alert_configs(
    active_only: bool = Query(
        False, description="Only return active configurations"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    service: AlertApplicationService = Depends(get_service),
) -> AlertConfigListResponse:
    """List all alert configurations."""
    if active_only:
        configs = await service.get_active_alert_configs(skip=skip, limit=limit)
    else:
        configs = await service.get_all_alert_configs(skip=skip, limit=limit)

    total = await service.count_alert_configs(active_only=active_only)

    return AlertConfigListResponse(
        data=[AlertConfigResponse.model_validate(c) for c in configs],
        total=total,
    )


@router.get("/alerts/config/{config_id}", response_model=AlertConfigResponse)
async def get_alert_config(
    config_id: UUID,
    service: AlertApplicationService = Depends(get_service),
) -> AlertConfigResponse:
    """Get details of a specific alert configuration."""
    config = await service.get_alert_config_by_id(config_id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert configuration {config_id} not found",
        )
    return AlertConfigResponse.model_validate(config)


@router.put("/alerts/config", response_model=AlertConfigResponse)
async def update_alert_config(
    config_id: UUID,
    request: AlertConfigRequest,
    service: AlertApplicationService = Depends(get_service),
) -> AlertConfigResponse:
    """Update an existing alert configuration."""
    try:
        config = await service.update_alert_config(
            config_id=config_id,
            name=request.name,
            pollutant=request.pollutant,
            warning_threshold=request.warning_threshold,
            high_threshold=request.high_threshold,
            critical_threshold=request.critical_threshold,
            duration_minutes=request.duration_minutes,
            notify_email=request.notify_email,
            notify_sms=request.notify_sms,
        )
        return AlertConfigResponse.model_validate(config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/alerts/config", response_model=AlertConfigResponse)
async def create_alert_config(
    request: AlertConfigRequest,
    service: AlertApplicationService = Depends(get_service),
) -> AlertConfigResponse:
    """Create a new alert configuration."""
    try:
        config = await service.create_alert_config(
            name=request.name,
            pollutant=request.pollutant,
            warning_threshold=request.warning_threshold,
            high_threshold=request.high_threshold,
            critical_threshold=request.critical_threshold,
            duration_minutes=request.duration_minutes,
            notify_email=request.notify_email,
            notify_sms=request.notify_sms,
        )
        return AlertConfigResponse.model_validate(config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


# =============================================================================
# Dashboard / Summary Endpoints
# =============================================================================


@router.get("/alerts/active", response_model=ActiveAlertsSummary)
async def get_active_alerts_count(
    service: AlertApplicationService = Depends(get_service),
) -> ActiveAlertsSummary:
    """Get count of active (open) alerts with breakdown."""
    total = await service.count_violations(status="OPEN")

    # Get breakdown by severity
    by_severity = {
        "WARNING": await service.count_violations(severity="WARNING", status="OPEN"),
        "HIGH": await service.count_violations(severity="HIGH", status="OPEN"),
        "CRITICAL": await service.count_violations(
            severity="CRITICAL", status="OPEN"
        ),
    }

    # Get breakdown by pollutant (fetch all open violations and count)
    violations = await service.get_active_violations(limit=1000)
    by_pollutant: dict[str, int] = {}
    for v in violations:
        pollutant = v.pollutant
        by_pollutant[pollutant] = by_pollutant.get(pollutant, 0) + 1

    return ActiveAlertsSummary(
        total_open_violations=total,
        by_severity=by_severity,
        by_pollutant=by_pollutant,
    )
