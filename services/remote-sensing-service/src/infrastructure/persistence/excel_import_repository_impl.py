"""SQLAlchemy implementation of ExcelImportRepository."""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.excel_import import (
    ExcelImport,
    ImportDataType,
    ImportStatus,
)
from ...domain.repositories.excel_import_repository import ExcelImportRepository
from .models import ExcelImportModel

logger = logging.getLogger(__name__)


class SQLAlchemyExcelImportRepository(ExcelImportRepository):
    """Repository implementation for Excel imports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, import_id: UUID) -> Optional[ExcelImport]:
        result = await self.session.execute(
            select(ExcelImportModel).where(ExcelImportModel.id == import_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_status(self, status: ImportStatus) -> List[ExcelImport]:
        result = await self.session.execute(
            select(ExcelImportModel)
            .where(ExcelImportModel.status == status.value)
            .order_by(ExcelImportModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_all(
        self, skip: int = 0, limit: int = 20
    ) -> List[ExcelImport]:
        result = await self.session.execute(
            select(ExcelImportModel)
            .order_by(ExcelImportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, record: ExcelImport) -> ExcelImport:
        model = self._to_model(record)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return self._to_entity(merged)

    async def delete(self, import_id: UUID) -> bool:
        result = await self.session.execute(
            delete(ExcelImportModel).where(ExcelImportModel.id == import_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    def _to_entity(self, model: ExcelImportModel) -> ExcelImport:
        return ExcelImport(
            id=model.id,
            filename=model.filename,
            data_type=ImportDataType(model.data_type),
            status=ImportStatus(model.status),
            file_path=model.file_path,
            record_count=model.record_count,
            processed_count=model.processed_count,
            error_count=model.error_count,
            errors=model.errors or [],
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    def _to_model(self, entity: ExcelImport) -> ExcelImportModel:
        return ExcelImportModel(
            id=entity.id,
            filename=entity.filename,
            data_type=entity.data_type.value,
            status=entity.status.value,
            file_path=entity.file_path,
            record_count=entity.record_count,
            processed_count=entity.processed_count,
            error_count=entity.error_count,
            errors=entity.errors,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )
