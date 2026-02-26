"""Factory API controller — HTTP endpoints for factory management.

Each endpoint maps an HTTP request to an application-layer command or query,
delegates to ``FactoryApplicationService``, and returns a Pydantic response
schema.  Authentication and role-based authorisation are enforced via FastAPI
dependencies from the shared auth library.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from shared.auth.dependencies import get_current_user, require_role
from shared.auth.models import UserClaims

from ...application.commands.create_factory_command import CreateFactoryCommand
from ...application.commands.resume_factory_command import ResumeFactoryCommand
from ...application.commands.suspend_factory_command import SuspendFactoryCommand
from ...application.commands.update_factory_command import UpdateFactoryCommand
from ...application.dto.factory_dto import FactoryDTO
from ...application.services.factory_application_service import (
    FactoryApplicationService,
)
from ...domain.exceptions.factory_exceptions import (
    FactoryAlreadyExistsError,
    FactoryAlreadySuspendedError,
    FactoryClosedError,
    FactoryDomainError,
    FactoryNotFoundError,
    FactoryNotSuspendedError,
    InvalidFactoryStatusError,
)
from .dependencies import get_factory_service
from .schemas import (
    EmissionLimitsResponse,
    ErrorResponse,
    FactoryCreateRequest,
    FactoryListResponse,
    FactoryResponse,
    FactoryUpdateRequest,
    MessageResponse,
    ResumeRequest,
    SuspendRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/factories", tags=["factories"])


# ---------------------------------------------------------------------------
# POST /factories — Create a new factory
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=FactoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new factory",
    description="Create a factory with its location, industry classification, and emission limits.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid payload"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        409: {"model": ErrorResponse, "description": "Duplicate registration number"},
    },
)
async def create_factory(
    request: FactoryCreateRequest,
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(require_role(["admin", "operator"])),
) -> FactoryResponse:
    """Register a new factory.

    Requires ``admin`` or ``operator`` role.
    """
    command = CreateFactoryCommand(
        name=request.name,
        registration_number=request.registration_number,
        industry_type=request.industry_type,
        latitude=request.latitude,
        longitude=request.longitude,
        emission_limits=request.emission_limits,
    )

    try:
        dto = await service.create_factory(command)
    except FactoryAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=exc.detail,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc),
        ) from exc

    return FactoryResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# GET /factories — List factories (paginated, filterable)
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=FactoryListResponse,
    summary="List factories",
    description="Retrieve a paginated list of factories with optional status filter.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def list_factories(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status (active, warning, critical, suspended, closed)",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(get_current_user),
) -> FactoryListResponse:
    """List all factories with optional filtering and pagination.

    Requires authentication (any role).
    """
    from ...application.queries.list_factories_query import ListFactoriesQuery

    query = ListFactoriesQuery(status=status_filter, skip=skip, limit=limit)
    dto = await service.list_factories(query)
    return FactoryListResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# GET /factories/{factory_id} — Get a single factory
# ---------------------------------------------------------------------------
@router.get(
    "/{factory_id}",
    response_model=FactoryResponse,
    summary="Get factory by ID",
    description="Retrieve detailed information about a specific factory.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Factory not found"},
    },
)
async def get_factory(
    factory_id: UUID,
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(get_current_user),
) -> FactoryResponse:
    """Retrieve a factory by its UUID.

    Requires authentication (any role).
    """
    try:
        dto = await service.get_factory(factory_id)
    except FactoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc

    return FactoryResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# PUT /factories/{factory_id} — Update factory
# ---------------------------------------------------------------------------
@router.put(
    "/{factory_id}",
    response_model=FactoryResponse,
    summary="Update a factory",
    description="Partially update factory details.  Only non-null fields are applied.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid payload or no changes"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Factory not found"},
    },
)
async def update_factory(
    factory_id: UUID,
    request: FactoryUpdateRequest,
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(require_role(["admin", "operator"])),
) -> FactoryResponse:
    """Update an existing factory.

    Requires ``admin`` or ``operator`` role.
    """
    command = UpdateFactoryCommand(
        factory_id=factory_id,
        name=request.name,
        industry_type=request.industry_type,
        latitude=request.latitude,
        longitude=request.longitude,
        emission_limits=request.emission_limits,
    )

    try:
        dto = await service.update_factory(command)
    except FactoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc
    except (ValueError, FactoryClosedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail if hasattr(exc, "detail") else str(exc),
        ) from exc

    return FactoryResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# DELETE /factories/{factory_id} — Delete (close) a factory
# ---------------------------------------------------------------------------
@router.delete(
    "/{factory_id}",
    response_model=MessageResponse,
    summary="Delete a factory",
    description="Permanently close/delete a factory.  This is irreversible.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Factory not found"},
    },
)
async def delete_factory(
    factory_id: UUID,
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(require_role(["admin"])),
) -> MessageResponse:
    """Delete (permanently close) a factory.

    Requires ``admin`` role.
    """
    try:
        await service.delete_factory(factory_id)
    except FactoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc

    logger.info("Factory deleted: %s by user %s", factory_id, user.user_id)
    return MessageResponse(message=f"Factory {factory_id} deleted successfully")


# ---------------------------------------------------------------------------
# GET /factories/{factory_id}/emissions — Get emission limits
# ---------------------------------------------------------------------------
@router.get(
    "/{factory_id}/emissions",
    response_model=EmissionLimitsResponse,
    summary="Get factory emission limits",
    description="Retrieve the emission limit configuration for a specific factory.",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Factory not found"},
    },
)
async def get_factory_emissions(
    factory_id: UUID,
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(get_current_user),
) -> EmissionLimitsResponse:
    """Retrieve emission limits for a factory.

    Requires authentication (any role).
    """
    try:
        dto = await service.get_factory(factory_id)
    except FactoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc

    return EmissionLimitsResponse(
        factory_id=dto.id,
        factory_name=dto.name,
        emission_limits=dto.emission_limits,
    )


# ---------------------------------------------------------------------------
# POST /factories/{factory_id}/suspend — Suspend a factory
# ---------------------------------------------------------------------------
@router.post(
    "/{factory_id}/suspend",
    response_model=FactoryResponse,
    summary="Suspend factory operations",
    description="Suspend a factory due to emission violations or other reasons.",
    responses={
        400: {"model": ErrorResponse, "description": "Factory already suspended or closed"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Factory not found"},
    },
)
async def suspend_factory(
    factory_id: UUID,
    request: SuspendRequest,
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(require_role(["admin", "inspector"])),
) -> FactoryResponse:
    """Suspend factory operations.

    Requires ``admin`` or ``inspector`` role.
    """
    command = SuspendFactoryCommand(
        factory_id=factory_id,
        reason=request.reason,
        suspended_by=request.suspended_by,
    )

    try:
        dto = await service.suspend_factory(command)
    except FactoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc
    except (
        FactoryAlreadySuspendedError,
        FactoryClosedError,
        InvalidFactoryStatusError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail,
        ) from exc

    return FactoryResponse.from_dto(dto)


# ---------------------------------------------------------------------------
# POST /factories/{factory_id}/resume — Resume a suspended factory
# ---------------------------------------------------------------------------
@router.post(
    "/{factory_id}/resume",
    response_model=FactoryResponse,
    summary="Resume factory operations",
    description="Lift the suspension on a previously suspended factory.",
    responses={
        400: {"model": ErrorResponse, "description": "Factory not suspended or closed"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Factory not found"},
    },
)
async def resume_factory(
    factory_id: UUID,
    request: ResumeRequest,
    service: FactoryApplicationService = Depends(get_factory_service),
    user: UserClaims = Depends(require_role(["admin", "inspector"])),
) -> FactoryResponse:
    """Resume a suspended factory.

    Requires ``admin`` or ``inspector`` role.
    """
    command = ResumeFactoryCommand(
        factory_id=factory_id,
        resumed_by=request.resumed_by,
        notes=request.notes,
    )

    try:
        dto = await service.resume_factory(command)
    except FactoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail,
        ) from exc
    except (
        FactoryNotSuspendedError,
        FactoryClosedError,
        InvalidFactoryStatusError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail,
        ) from exc

    return FactoryResponse.from_dto(dto)
