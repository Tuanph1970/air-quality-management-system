"""Create envisoft_fetch_logs table.

Tracks every fetch attempt by date + station so we can:
- Know which days/stations were successfully fetched
- Detect missing days and auto-retry on next run
- Provide a /retry endpoint for manual catch-up

Revision ID: 002_create_fetch_logs
Revises: 001_create_hourly_readings
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_create_fetch_logs"
down_revision: Union[str, None] = "001_create_hourly_readings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "envisoft_fetch_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        # The date this fetch was FOR (not when it ran)
        sa.Column("fetch_date", sa.Date, nullable=False, index=True),
        # Which station was targeted
        sa.Column("station_id", sa.String(64), nullable=False),
        # Attempt number within this date+station (1 = first try)
        sa.Column("attempt", sa.Integer, nullable=False, default=1),
        # Outcome
        sa.Column("status", sa.String(20), nullable=False, default="pending"),  # pending | success | partial | failed
        # How many records were upserted this attempt
        sa.Column("records_count", sa.Integer, nullable=True),
        # Human-readable error if failed
        sa.Column("error_message", sa.Text, nullable=True),
        # When this attempt ran
        sa.Column("started_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        # Which Excel file was used (if any)
        sa.Column("excel_path", sa.String(500), nullable=True),
    )

    # Unique constraint: one row per date+station+attempt
    op.create_index(
        "idx_fetchlog_date_station_attempt",
        "envisoft_fetch_logs",
        ["fetch_date", "station_id", "attempt"],
        unique=True,
    )
    # Index for finding missing dates: date + success
    op.create_index(
        "idx_fetchlog_date_status",
        "envisoft_fetch_logs",
        ["fetch_date", "status"],
    )
    # Index for finding failed attempts per date+station (to get latest attempt #)
    op.create_index(
        "idx_fetchlog_date_station",
        "envisoft_fetch_logs",
        ["fetch_date", "station_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_fetchlog_date_station", table_name="envisoft_fetch_logs")
    op.drop_index("idx_fetchlog_date_status", table_name="envisoft_fetch_logs")
    op.drop_index("idx_fetchlog_date_station_attempt", table_name="envisoft_fetch_logs")
    op.drop_table("envisoft_fetch_logs")
