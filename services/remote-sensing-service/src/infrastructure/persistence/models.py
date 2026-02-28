"""SQLAlchemy ORM models for the remote-sensing service.

These models define the relational schema that backs the ``SatelliteData``,
``FusedData``, and ``ExcelImport`` domain entities.  Mapping between ORM
models and domain objects is handled by the repository implementations.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Satellite Data
# ---------------------------------------------------------------------------
class SatelliteDataModel(Base):
    """Relational representation of a SatelliteData entity."""

    __tablename__ = "satellite_data"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False)
    observation_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    fetch_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    # Bounding box stored as JSON: {north, south, east, west}
    bbox: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Grid cells stored as JSON array: [{lat, lon, value, uncertainty}, ...]
    grid_cells: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    quality_flag: Mapped[str] = mapped_column(
        String(20), nullable=False, default="GOOD",
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
    )
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_satellite_data_source", "source"),
        Index("ix_satellite_data_type", "data_type"),
        Index("ix_satellite_data_observation_time", "observation_time"),
        Index("ix_satellite_data_source_type", "source", "data_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<SatelliteDataModel id={self.id} source={self.source} "
            f"type={self.data_type}>"
        )


# ---------------------------------------------------------------------------
# Fused Data
# ---------------------------------------------------------------------------
class FusedDataModel(Base):
    """Relational representation of a FusedData entity."""

    __tablename__ = "fused_data"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    sources_used: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    bbox: Mapped[dict] = mapped_column(JSON, nullable=False)
    time_range_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    time_range_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # Data points stored as JSON array
    data_points: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    average_confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
    )
    pollutant: Mapped[str] = mapped_column(String(20), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    __table_args__ = (
        Index("ix_fused_data_pollutant", "pollutant"),
        Index("ix_fused_data_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<FusedDataModel id={self.id} pollutant={self.pollutant} "
            f"confidence={self.average_confidence:.2f}>"
        )


# ---------------------------------------------------------------------------
# Excel Import
# ---------------------------------------------------------------------------
class ExcelImportModel(Base):
    """Relational representation of an ExcelImport entity."""

    __tablename__ = "excel_imports"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING",
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)

    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    __table_args__ = (
        Index("ix_excel_imports_status", "status"),
        Index("ix_excel_imports_data_type", "data_type"),
        Index("ix_excel_imports_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ExcelImportModel id={self.id} filename={self.filename!r} "
            f"status={self.status}>"
        )
