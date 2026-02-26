"""Pydantic request/response schemas."""
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class ViolationResponse(BaseModel):
    id: UUID
    factory_id: UUID
    pollutant: str
    measured_value: float
    threshold: float
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None


class ViolationListResponse(BaseModel):
    data: List[ViolationResponse]
    total: int


class ResolveViolationRequest(BaseModel):
    resolved_by: UUID
