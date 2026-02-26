"""Create factory and suspension tables.

Revision ID: 001_create_factory_tables
Revises: None
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision: str = "001_create_factory_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # factories table
    # ------------------------------------------------------------------
    op.create_table(
        "factories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "registration_number",
            sa.String(100),
            unique=True,
            nullable=False,
        ),
        sa.Column("industry_type", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("emission_limits", JSON, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
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

    # Indexes for factories
    op.create_index("ix_factories_status", "factories", ["status"])
    op.create_index("ix_factories_industry_type", "factories", ["industry_type"])
    op.create_index(
        "ix_factories_registration_number",
        "factories",
        ["registration_number"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # suspensions table
    # ------------------------------------------------------------------
    op.create_table(
        "suspensions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "factory_id",
            UUID(as_uuid=True),
            sa.ForeignKey("factories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("suspended_by", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "suspended_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resumed_by", UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )

    # Indexes for suspensions
    op.create_index("ix_suspensions_factory_id", "suspensions", ["factory_id"])
    op.create_index("ix_suspensions_is_active", "suspensions", ["is_active"])
    op.create_index(
        "ix_suspensions_factory_active",
        "suspensions",
        ["factory_id", "is_active"],
    )


def downgrade() -> None:
    # Drop suspensions first (FK dependency).
    op.drop_index("ix_suspensions_factory_active", table_name="suspensions")
    op.drop_index("ix_suspensions_is_active", table_name="suspensions")
    op.drop_index("ix_suspensions_factory_id", table_name="suspensions")
    op.drop_table("suspensions")

    # Drop factories.
    op.drop_index("ix_factories_registration_number", table_name="factories")
    op.drop_index("ix_factories_industry_type", table_name="factories")
    op.drop_index("ix_factories_status", table_name="factories")
    op.drop_table("factories")
