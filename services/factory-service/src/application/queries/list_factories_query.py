"""Query to list factories with filters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ListFactoriesQuery:
    """Query to retrieve a paginated, filterable list of factories."""

    status: Optional[str] = None
    industry_type: Optional[str] = None
    skip: int = 0
    limit: int = 20

    def validate(self) -> None:
        """Raise ``ValueError`` if pagination values are out of range."""
        if self.skip < 0:
            raise ValueError("skip must be non-negative")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("limit must be between 1 and 100")
