"""Create envisoft_hourly_readings table.

Revision ID: 001_create_hourly_readings
Revises: None
Create Date: 2026-04-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_create_hourly_readings"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "envisoft_hourly_readings",
        # Primary / identity
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(64), nullable=False, index=True),
        # Time
        sa.Column("measured_at", sa.DateTime, nullable=False, index=True),
        sa.Column("fetched_at", sa.DateTime, nullable=False, server_default=sa.text("now())),
        # Pollutants (µg/m³)
        sa.Column("pm25", sa.Float, nullable=True),
        sa.Column("pm10", sa.Float, nullable=True),
        sa.Column("no2", sa.Float, nullable=True),
        sa.Column("so2", sa.Float, nullable=True),
        sa.Column("co", sa.Float, nullable=True),
        sa.Column("o3", sa.Float, nullable=True),
        # Air Quality Index
        sa.Column("aqi", sa.Integer, nullable=True),
        sa.Column("aqi_category", sa.String(50), nullable=True),
        # Environmental
        sa.Column("temperature", sa.Float, nullable=True),
        sa.Column("humidity", sa.Float, nullable=True),
        # Wind
        sa.Column("wind_speed", sa.Float, nullable=True),
        sa.Column("wind_direction", sa.Float, nullable=True),
        # Additional fields
        sa.Column("no_value", sa.Float, nullable=True),
        sa.Column("nox_value", sa.Float, nullable=True),
        sa.Column("total_pollutant", sa.Float, nullable=True),
        sa.Column("atmospheric_pressure", sa.Float, nullable=True),
        sa.Column("noise_level", sa.Float, nullable=True),
        # Station metadata (from EnviSoft)
        sa.Column("station_code", sa.String(100), nullable=True),
        sa.Column("station_name", sa.String(255), nullable=True),
        # Excel path (for reference/correction)
        sa.Column("excel_path", sa.String(500), nullable=True),
    )

    # Indexes
    op.create_index("idx_reading_station_measured", "envisoft_hourly_readings",
                    ["station_id", "measured_at"], unique=True)
    op.create_index("idx_reading_measured", "envisoft_hourly_readings", ["measured_at"])


def downgrade() -> None:
    op.drop_index("idx_reading_measured", table_name="envisoft_hourly_readings")
    op.drop_index("idx_reading_station_measured", table_name="envisoft_hourly_readings")
    op.drop_table("envisoft_hourly_readings")
