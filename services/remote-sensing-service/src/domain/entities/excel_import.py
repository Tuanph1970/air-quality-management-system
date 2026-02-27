"""Excel file import record entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


class ImportStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportDataType(Enum):
    HISTORICAL_READINGS = "historical_readings"
    FACTORY_RECORDS = "factory_records"
    SENSOR_METADATA = "sensor_metadata"


@dataclass
class ExcelImport:
    """Entity: Excel file import record."""

    id: UUID
    filename: str
    data_type: ImportDataType
    status: ImportStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    record_count: int = 0
    processed_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    file_path: Optional[str] = None

    _events: list = field(default_factory=list, repr=False)

    @classmethod
    def create(
        cls, filename: str, data_type: ImportDataType, file_path: str
    ) -> "ExcelImport":
        """Factory method to create ExcelImport."""
        return cls(
            id=uuid4(),
            filename=filename,
            data_type=data_type,
            status=ImportStatus.PENDING,
            created_at=datetime.utcnow(),
            file_path=file_path,
        )

    def start_processing(self, total_records: int) -> None:
        """Transition to processing state."""
        self.status = ImportStatus.PROCESSING
        self.record_count = total_records

    def record_processed(self) -> None:
        """Increment processed count."""
        self.processed_count += 1

    def record_error(self, error: str) -> None:
        """Record a processing error."""
        self.error_count += 1
        self.errors.append(error)

    def complete(self) -> None:
        """Mark import as completed and emit event."""
        from shared.events.satellite_events import ExcelDataImported

        self.status = ImportStatus.COMPLETED
        self.completed_at = datetime.utcnow()

        self._events.append(
            ExcelDataImported(
                event_id=uuid4(),
                occurred_at=datetime.utcnow(),
                import_id=self.id,
                filename=self.filename,
                record_count=self.processed_count,
                data_type=self.data_type.value,
            )
        )

    def fail(self, error: str) -> None:
        """Mark import as failed."""
        self.status = ImportStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.errors.append(error)

    def collect_events(self) -> list:
        """Collect and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events
