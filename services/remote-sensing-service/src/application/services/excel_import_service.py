"""Application service for Excel data import.

Handles file upload, validation, parsing, and event publication
for historical readings and factory records imported from Excel.
"""

from __future__ import annotations

import logging
import os
import shutil
from typing import List, Optional
from uuid import UUID

from fastapi import UploadFile

from ...domain.entities.excel_import import (
    ExcelImport,
    ImportDataType,
    ImportStatus,
)
from ...domain.repositories.excel_import_repository import ExcelImportRepository
from ...infrastructure.parsers.excel_parser import ExcelParser, ValidationResult
from ..dto.excel_import_dto import ExcelImportDTO
from shared.messaging.publisher import RabbitMQPublisher
from shared.messaging.config import SATELLITE_EXCHANGE

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/data/uploads"


class ExcelImportService:
    """Application service for Excel data import."""

    def __init__(
        self,
        repository: ExcelImportRepository,
        parser: ExcelParser,
        event_publisher: RabbitMQPublisher,
        upload_dir: str = UPLOAD_DIR,
    ):
        self.repository = repository
        self.parser = parser
        self.event_publisher = event_publisher
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    async def validate_file(
        self, file: UploadFile, data_type: ImportDataType
    ) -> ValidationResult:
        """Validate an Excel file format before importing."""
        temp_path = os.path.join(self.upload_dir, f"temp_{file.filename}")
        try:
            with open(temp_path, "wb") as fh:
                shutil.copyfileobj(file.file, fh)

            if data_type == ImportDataType.HISTORICAL_READINGS:
                columns = ExcelParser.HISTORICAL_READINGS_COLUMNS
            elif data_type == ImportDataType.FACTORY_RECORDS:
                columns = ExcelParser.FACTORY_RECORDS_COLUMNS
            else:
                columns = ExcelParser.HISTORICAL_READINGS_COLUMNS

            return self.parser.validate_format(temp_path, columns)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # ------------------------------------------------------------------
    # Import operations
    # ------------------------------------------------------------------
    async def import_historical_readings(
        self, file: UploadFile
    ) -> ExcelImportDTO:
        """Import historical air-quality readings from an Excel file."""
        file_path = os.path.join(self.upload_dir, file.filename)
        with open(file_path, "wb") as fh:
            shutil.copyfileobj(file.file, fh)

        import_record = ExcelImport.create(
            filename=file.filename,
            data_type=ImportDataType.HISTORICAL_READINGS,
            file_path=file_path,
        )

        try:
            records = self.parser.parse_historical_readings(file_path)
            import_record.start_processing(len(records))

            for record in records:
                try:
                    # TODO: forward to sensor-service or persist locally
                    import_record.record_processed()
                except Exception as exc:
                    import_record.record_error(str(exc))

            import_record.complete()
            logger.info(
                "Import completed: %s — %d/%d records",
                file.filename,
                import_record.processed_count,
                import_record.record_count,
            )
        except Exception as exc:
            import_record.fail(str(exc))
            logger.error("Import failed: %s — %s", file.filename, exc)

        saved = await self.repository.save(import_record)

        for event in saved.collect_events():
            await self.event_publisher.publish(event, SATELLITE_EXCHANGE)

        return ExcelImportDTO.from_entity(saved)

    async def import_factory_records(
        self, file: UploadFile
    ) -> ExcelImportDTO:
        """Import factory records from an Excel file."""
        file_path = os.path.join(self.upload_dir, file.filename)
        with open(file_path, "wb") as fh:
            shutil.copyfileobj(file.file, fh)

        import_record = ExcelImport.create(
            filename=file.filename,
            data_type=ImportDataType.FACTORY_RECORDS,
            file_path=file_path,
        )

        try:
            records = self.parser.parse_factory_records(file_path)
            import_record.start_processing(len(records))

            for record in records:
                try:
                    # TODO: forward to factory-service or persist locally
                    import_record.record_processed()
                except Exception as exc:
                    import_record.record_error(str(exc))

            import_record.complete()
            logger.info(
                "Factory import completed: %s — %d/%d records",
                file.filename,
                import_record.processed_count,
                import_record.record_count,
            )
        except Exception as exc:
            import_record.fail(str(exc))
            logger.error("Factory import failed: %s — %s", file.filename, exc)

        saved = await self.repository.save(import_record)

        for event in saved.collect_events():
            await self.event_publisher.publish(event, SATELLITE_EXCHANGE)

        return ExcelImportDTO.from_entity(saved)

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------
    async def get_import_status(
        self, import_id: UUID
    ) -> Optional[ExcelImportDTO]:
        """Get the status of an import by ID."""
        record = await self.repository.get_by_id(import_id)
        return ExcelImportDTO.from_entity(record) if record else None

    async def list_imports(
        self, skip: int = 0, limit: int = 20
    ) -> List[ExcelImportDTO]:
        """List all import records."""
        records = await self.repository.list_all(skip=skip, limit=limit)
        return [ExcelImportDTO.from_entity(r) for r in records]

    async def get_imports_by_status(
        self, status: ImportStatus
    ) -> List[ExcelImportDTO]:
        """List imports filtered by status."""
        records = await self.repository.get_by_status(status)
        return [ExcelImportDTO.from_entity(r) for r in records]
