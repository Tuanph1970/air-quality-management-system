"""Create sensor and reading tables with TimescaleDB hypertable.

Revision ID: 001_create_sensor_tables
Revises: None
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision: str = "001_create_sensor_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # sensors table
    # ------------------------------------------------------------------
    op.create_table(
        "sensors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "serial_number",
            sa.String(100),
            unique=True,
            nullable=False,
        ),
        sa.Column("sensor_type", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False, server_default=""),
        sa.Column("factory_id", UUID(as_uuid=True), nullable=True),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("calibration_params", JSON, nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="ONLINE",
        ),
        sa.Column("installation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_calibration", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Indexes for sensors
    op.create_index(
        "ix_sensors_serial_number", "sensors", ["serial_number"], unique=True,
    )
    op.create_index("ix_sensors_factory_id", "sensors", ["factory_id"])
    op.create_index("ix_sensors_status", "sensors", ["status"])
    op.create_index("ix_sensors_sensor_type", "sensors", ["sensor_type"])

    # ------------------------------------------------------------------
    # readings table
    # ------------------------------------------------------------------
    op.create_table(
        "readings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("sensor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("factory_id", UUID(as_uuid=True), nullable=True),
        # Pollutant concentrations
        sa.Column("pm25", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("pm10", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("co", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("co2", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("no2", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("nox", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("so2", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("o3", sa.Float, nullable=False, server_default="0.0"),
        # Environmental
        sa.Column("temperature", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("humidity", sa.Float, nullable=False, server_default="0.0"),
        # Calculated
        sa.Column("aqi", sa.Integer, nullable=False, server_default="0"),
        # Time dimension (used by TimescaleDB hypertable)
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Indexes for readings
    op.create_index("ix_readings_sensor_id", "readings", ["sensor_id"])
    op.create_index("ix_readings_factory_id", "readings", ["factory_id"])
    op.create_index("ix_readings_timestamp", "readings", ["timestamp"])
    op.create_index(
        "ix_readings_sensor_timestamp", "readings", ["sensor_id", "timestamp"],
    )

    # ------------------------------------------------------------------
    # TimescaleDB hypertable conversion
    # ------------------------------------------------------------------
    # Convert the readings table into a TimescaleDB hypertable partitioned
    # by the ``timestamp`` column.  The ``if_not_exists`` parameter makes
    # this safe to re-run.
    op.execute(
        "SELECT create_hypertable('readings', 'timestamp', "
        "if_not_exists => TRUE, migrate_data => TRUE)"
    )


def downgrade() -> None:
    # Drop readings first (no FK, but logically depends on sensors).
    op.drop_index("ix_readings_sensor_timestamp", table_name="readings")
    op.drop_index("ix_readings_timestamp", table_name="readings")
    op.drop_index("ix_readings_factory_id", table_name="readings")
    op.drop_index("ix_readings_sensor_id", table_name="readings")
    op.drop_table("readings")

    # Drop sensors.
    op.drop_index("ix_sensors_sensor_type", table_name="sensors")
    op.drop_index("ix_sensors_status", table_name="sensors")
    op.drop_index("ix_sensors_factory_id", table_name="sensors")
    op.drop_index("ix_sensors_serial_number", table_name="sensors")
    op.drop_table("sensors")
