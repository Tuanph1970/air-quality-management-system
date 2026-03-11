"""SQLAlchemy models for WRF Service."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


class Base(MappedAsDataclass, DeclarativeBase):
    """Base class for all models."""

    pass


class WRFSimulationModel(Base):
    """SQLAlchemy model for WRF simulations."""

    __tablename__ = "wrf_simulations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        init=False,
        default_factory=lambda: UUID(int=0),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    progress_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )

    # Configuration stored as JSON
    config_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )

    # File paths
    output_file_path: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    gfs_data_path: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    wrf_output_files: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, init=False, default_factory=datetime.utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "config_json": self.config_json,
            "output_file_path": self.output_file_path,
            "gfs_data_path": self.gfs_data_path,
            "wrf_output_files": self.wrf_output_files,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at else None,
        }
