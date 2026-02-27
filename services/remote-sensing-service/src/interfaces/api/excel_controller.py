"""Excel import API controller.

Provides endpoints for uploading, validating, and importing data from
Excel files (historical readings and factory records).
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status

from ...application.services.excel_import_service import ExcelImportService
from ...domain.entities.excel_import import ImportDataType, ImportStatus
from .dependencies import get_excel_import_service
from .schemas import (
    ExcelImportListResponse,
    ExcelImportResponse,
    ExcelValidationResponse,
    ImportDataTypeEnum,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/excel", tags=["excel"])


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
@router.post(
    "/validate",
    response_model=ExcelValidationResponse,
    summary="Validate Excel file format",
)
async def validate_excel_file(
    file: UploadFile = File(...),
    data_type: ImportDataTypeEnum = Query(
        ImportDataTypeEnum.HISTORICAL_READINGS,
        description="Type of data in the Excel file",
    ),
    service: ExcelImportService = Depends(get_excel_import_service),
):
    """Validate an Excel file's format and column structure before import."""
    import_type = ImportDataType(data_type.value)
    result = await service.validate_file(file, import_type)
    return ExcelValidationResponse(
        is_valid=result.is_valid,
        errors=result.errors,
        warnings=result.warnings,
        row_count=result.row_count,
        columns_found=result.columns_found,
    )


# ---------------------------------------------------------------------------
# Import endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/import/readings",
    response_model=ExcelImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import historical readings from Excel",
)
async def import_historical_readings(
    file: UploadFile = File(...),
    service: ExcelImportService = Depends(get_excel_import_service),
):
    """Import historical air quality readings from an Excel file."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be Excel format (.xlsx or .xls)",
        )

    result = await service.import_historical_readings(file)
    return result.to_dict()


@router.post(
    "/import/factories",
    response_model=ExcelImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import factory records from Excel",
)
async def import_factory_records(
    file: UploadFile = File(...),
    service: ExcelImportService = Depends(get_excel_import_service),
):
    """Import factory records from an Excel file."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be Excel format (.xlsx or .xls)",
        )

    result = await service.import_factory_records(file)
    return result.to_dict()


# ---------------------------------------------------------------------------
# Query endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/imports",
    response_model=ExcelImportListResponse,
    summary="List all imports",
)
async def list_imports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    service: ExcelImportService = Depends(get_excel_import_service),
):
    """List all import records with optional status filter."""
    if status_filter:
        try:
            import_status = ImportStatus(status_filter.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )
        records = await service.get_imports_by_status(import_status)
        data = [r.to_dict() for r in records]
    else:
        records = await service.list_imports(skip=skip, limit=limit)
        data = [r.to_dict() for r in records]

    return {"data": data, "total": len(data)}


@router.get(
    "/imports/{import_id}",
    response_model=ExcelImportResponse,
    summary="Get import status",
)
async def get_import_status(
    import_id: UUID,
    service: ExcelImportService = Depends(get_excel_import_service),
):
    """Get the status and details of a specific import by ID."""
    result = await service.get_import_status(import_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found",
        )
    return result.to_dict()
