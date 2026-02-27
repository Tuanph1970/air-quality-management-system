"""Excel import Data Transfer Object."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ...domain.entities.excel_import import ExcelImport


@dataclass
class ExcelImportDTO:
    """Read-only projection of an ExcelImport entity."""

    id: UUID
    filename: str
    data_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    record_count: int = 0
    processed_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)

    @classmethod
    def from_entity(cls, entity: ExcelImport) -> "ExcelImportDTO":
        return cls(
            id=entity.id,
            filename=entity.filename,
            data_type=entity.data_type.value,
            status=entity.status.value,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
            record_count=entity.record_count,
            processed_count=entity.processed_count,
            error_count=entity.error_count,
            errors=entity.errors[:],
        )

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "filename": self.filename,
            "data_type": self.data_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "record_count": self.record_count,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "errors": self.errors,
        }
