"""Pydantic request/response schemas."""
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime


class FactoryCreateRequest(BaseModel):
    name: str
    registration_number: str
    industry_type: str
    latitude: float
    longitude: float
    max_emissions: Dict


class FactoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    industry_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    max_emissions: Optional[Dict] = None


class SuspendRequest(BaseModel):
    reason: str
    suspended_by: UUID


class FactoryResponse(BaseModel):
    id: UUID
    name: str
    registration_number: str
    industry_type: str
    latitude: float
    longitude: float
    max_emissions: Dict
    operational_status: str
    created_at: datetime
    updated_at: datetime


class FactoryListResponse(BaseModel):
    data: List[FactoryResponse]
    total: int
