"""Module A Session Table Update

Revision ID: 003_module_a_session_update
Revises: 002_module_c_summary_update
Create Date: 2026-09-04 08:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_module_a_session_update'
down_revision: Union[str, None] = '002_module_c_summary_update'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('lifecycle_status', sa.String(length=50), nullable=False, server_default='CREATED'))
    op.add_column('sessions', sa.Column('mode', sa.String(length=20), nullable=False, server_default='MODERN'))
    op.add_column('sessions', sa.Column('disclaimer_acknowledged', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('sessions', sa.Column('disclaimer_acknowledged_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('sessions', sa.Column('socrates_state', sa.String(length=50), nullable=True, server_default='SITE'))
    op.add_column('sessions', sa.Column('structured_history', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('sessions', sa.Column('safety_status', sa.String(length=50), nullable=False, server_default='SAFE'))
    op.add_column('sessions', sa.Column('safety_alerts', sa.JSON(), nullable=False, server_default='{}'))
    op.create_index(op.f('ix_sessions_lifecycle_status'), 'sessions', ['lifecycle_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sessions_lifecycle_status'), table_name='sessions')
    op.drop_column('sessions', 'safety_alerts')
    op.drop_column('sessions', 'safety_status')
    op.drop_column('sessions', 'structured_history')
    op.drop_column('sessions', 'socrates_state')
    op.drop_column('sessions', 'disclaimer_acknowledged_at')
    op.drop_column('sessions', 'disclaimer_acknowledged')
    op.drop_column('sessions', 'mode')
    op.drop_column('sessions', 'lifecycle_status')
