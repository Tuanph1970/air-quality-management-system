"""Add radiation column to envisoft_hourly_readings.

The Envisoft Excel export includes a Radiation (W/m2) column that was parsed
but not stored because the column was missing from the model. This caused
KeyError: 'radiation' in bulk_upsert when radiation values were non-null.

Revision ID: 003_add_radiation_column
Revises: 002_create_fetch_logs
Create Date: 2026-04-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_add_radiation_column"
down_revision: Union[str, None] = "002_create_fetch_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "envisoft_hourly_readings",
        sa.Column("radiation", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("envisoft_hourly_readings", "radiation")
