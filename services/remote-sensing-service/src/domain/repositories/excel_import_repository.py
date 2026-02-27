"""Excel import repository interface (port)."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.excel_import import ExcelImport, ImportStatus


class ExcelImportRepository(ABC):
    """Repository interface for Excel import records."""

    @abstractmethod
    async def get_by_id(self, import_id: UUID) -> Optional[ExcelImport]:
        pass

    @abstractmethod
    async def get_by_status(self, status: ImportStatus) -> List[ExcelImport]:
        pass

    @abstractmethod
    async def list_all(
        self, skip: int = 0, limit: int = 20
    ) -> List[ExcelImport]:
        pass

    @abstractmethod
    async def save(self, excel_import: ExcelImport) -> ExcelImport:
        pass

    @abstractmethod
    async def delete(self, import_id: UUID) -> bool:
        pass
