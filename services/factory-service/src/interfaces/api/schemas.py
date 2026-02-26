"""Pydantic request/response schemas for the factory API.

These schemas handle HTTP serialisation, validation, and OpenAPI
documentation.  They are the *only* layer that uses Pydantic — the
domain and application layers use plain dataclasses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# Request schemas
# =========================================================================

class FactoryCreateRequest(BaseModel):
    """Payload for creating a new factory."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Viet Steel Manufacturing",
                "registration_number": "REG-2024-001",
                "industry_type": "Steel",
                "latitude": 21.0285,
                "longitude": 105.8542,
                "emission_limits": {
                    "pm25_limit": 50.0,
                    "pm10_limit": 100.0,
                    "co_limit": 10.0,
                    "no2_limit": 40.0,
                    "so2_limit": 20.0,
                    "o3_limit": 60.0,
                },
            }
        }
    )

    name: str = Field(
        ..., min_length=1, max_length=255,
        description="Official factory name",
    )
    registration_number: str = Field(
        ..., min_length=1, max_length=100,
        description="Unique government registration number",
    )
    industry_type: str = Field(
        ..., min_length=1, max_length=100,
        description="Industry classification (e.g. Steel, Chemical, Textile)",
    )
    latitude: float = Field(
        ..., ge=-90, le=90,
        description="GPS latitude in decimal degrees",
    )
    longitude: float = Field(
        ..., ge=-180, le=180,
        description="GPS longitude in decimal degrees",
    )
    emission_limits: Dict[str, float] = Field(
        default_factory=dict,
        description="Maximum pollutant limits in µg/m³",
    )


class FactoryUpdateRequest(BaseModel):
    """Payload for partially updating a factory.  Only non-null fields are applied."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Viet Steel Manufacturing (Updated)",
                "emission_limits": {"pm25_limit": 45.0, "pm10_limit": 90.0},
            }
        }
    )

    name: Optional[str] = Field(
        None, min_length=1, max_length=255,
        description="Updated factory name",
    )
    industry_type: Optional[str] = Field(
        None, min_length=1, max_length=100,
        description="Updated industry classification",
    )
    latitude: Optional[float] = Field(
        None, ge=-90, le=90,
        description="Updated GPS latitude",
    )
    longitude: Optional[float] = Field(
        None, ge=-180, le=180,
        description="Updated GPS longitude",
    )
    emission_limits: Optional[Dict[str, float]] = Field(
        None,
        description="Updated pollutant limits",
    )


class SuspendRequest(BaseModel):
    """Payload for suspending a factory."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reason": "Exceeded PM2.5 emission limits for 3 consecutive days",
                "suspended_by": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    )

    reason: str = Field(
        ..., min_length=1, max_length=500,
        description="Reason for the suspension",
    )
    suspended_by: UUID = Field(
        ...,
        description="User ID of the authority ordering the suspension",
    )


class ResumeRequest(BaseModel):
    """Payload for resuming a suspended factory."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resumed_by": "550e8400-e29b-41d4-a716-446655440000",
                "notes": "Emissions returned to acceptable levels after corrective action",
            }
        }
    )

    resumed_by: UUID = Field(
        ...,
        description="User ID of the authority lifting the suspension",
    )
    notes: str = Field(
        "",
        max_length=1000,
        description="Optional notes about the resumption",
    )


# =========================================================================
# Response schemas
# =========================================================================

class FactoryResponse(BaseModel):
    """Single factory resource."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    registration_number: str
    industry_type: str
    latitude: float
    longitude: float
    emission_limits: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto) -> FactoryResponse:
        """Map a ``FactoryDTO`` to a response schema."""
        return cls(
            id=dto.id,
            name=dto.name,
            registration_number=dto.registration_number,
            industry_type=dto.industry_type,
            latitude=dto.latitude,
            longitude=dto.longitude,
            emission_limits=dto.emission_limits,
            status=dto.status,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class FactoryListResponse(BaseModel):
    """Paginated list of factories."""

    items: List[FactoryResponse]
    total: int
    skip: int
    limit: int

    @classmethod
    def from_dto(cls, dto) -> FactoryListResponse:
        """Map a ``FactoryListDTO`` to a response schema."""
        return cls(
            items=[FactoryResponse.from_dto(f) for f in dto.items],
            total=dto.total,
            skip=dto.skip,
            limit=dto.limit,
        )


class EmissionLimitsResponse(BaseModel):
    """Emission limits for a single factory."""

    factory_id: UUID
    factory_name: str
    emission_limits: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all error handlers."""

    detail: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "Factory not found: <id>"}}
    )


class MessageResponse(BaseModel):
    """Simple success/info message."""

    message: str
