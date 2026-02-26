"""Query to list factories with filters."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListFactoriesQuery:
    status: Optional[str] = None
    skip: int = 0
    limit: int = 20
