"""Query to get violations."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class GetViolationsQuery:
    factory_id: Optional[UUID] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    skip: int = 0
    limit: int = 20
