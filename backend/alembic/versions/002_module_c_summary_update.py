"""Module C Summary Table Update

Revision ID: 002_module_c_summary_update
Revises: 001_initial_schema
Create Date: 2026-09-03 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_module_c_summary_update'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('summaries', sa.Column('workflow_status', sa.String(length=50), nullable=False, server_default='NOT_GENERATED'))
    op.add_column('summaries', sa.Column('structured_summary', sa.JSON(), nullable=True))
    op.add_column('summaries', sa.Column('physician_edited_summary', sa.JSON(), nullable=True))
    op.add_column('summaries', sa.Column('generation_error', sa.Text(), nullable=True))
    op.add_column('summaries', sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('summaries', sa.Column('accepted_by', sa.String(length=100), nullable=True))
    op.add_column('summaries', sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('summaries', sa.Column('rejected_reason', sa.Text(), nullable=True))
    op.create_index(op.f('ix_summaries_workflow_status'), 'summaries', ['workflow_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_summaries_workflow_status'), table_name='summaries')
    op.drop_column('summaries', 'rejected_reason')
    op.drop_column('summaries', 'rejected_at')
    op.drop_column('summaries', 'accepted_by')
    op.drop_column('summaries', 'accepted_at')
    op.drop_column('summaries', 'generation_error')
    op.drop_column('summaries', 'physician_edited_summary')
    op.drop_column('summaries', 'structured_summary')
    op.drop_column('summaries', 'workflow_status')
