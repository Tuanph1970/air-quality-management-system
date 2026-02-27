"""Create violations and alert_configs tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create violations and alert_configs tables."""
    
    # Create violations table
    op.create_table(
        'violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('factory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sensor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pollutant', sa.String(length=20), nullable=False),
        sa.Column('measured_value', sa.Float, nullable=False),
        sa.Column('permitted_value', sa.Float, nullable=False),
        sa.Column('exceedance_percentage', sa.Float, nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_taken', sa.Text, nullable=False, server_default=''),
        sa.Column('notes', sa.Text, nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for violations table
    op.create_index('ix_violations_factory_id', 'violations', ['factory_id'])
    op.create_index('ix_violations_sensor_id', 'violations', ['sensor_id'])
    op.create_index('ix_violations_status', 'violations', ['status'])
    op.create_index('ix_violations_severity', 'violations', ['severity'])
    op.create_index(
        'ix_violations_factory_status',
        'violations',
        ['factory_id', 'status']
    )
    
    # Create alert_configs table
    op.create_table(
        'alert_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('pollutant', sa.String(length=20), nullable=False),
        sa.Column('warning_threshold', sa.Float, nullable=False),
        sa.Column('high_threshold', sa.Float, nullable=False),
        sa.Column('critical_threshold', sa.Float, nullable=False),
        sa.Column('duration_minutes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('notify_email', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('notify_sms', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pollutant')
    )
    
    # Create indexes for alert_configs table
    op.create_index('ix_alert_configs_pollutant', 'alert_configs', ['pollutant'])
    op.create_index('ix_alert_configs_is_active', 'alert_configs', ['is_active'])


def downgrade() -> None:
    """Drop violations and alert_configs tables."""
    op.drop_index('ix_alert_configs_is_active', table_name='alert_configs')
    op.drop_index('ix_alert_configs_pollutant', table_name='alert_configs')
    op.drop_table('alert_configs')
    
    op.drop_index('ix_violations_factory_status', table_name='violations')
    op.drop_index('ix_violations_severity', table_name='violations')
    op.drop_index('ix_violations_status', table_name='violations')
    op.drop_index('ix_violations_sensor_id', table_name='violations')
    op.drop_index('ix_violations_factory_id', table_name='violations')
    op.drop_table('violations')
