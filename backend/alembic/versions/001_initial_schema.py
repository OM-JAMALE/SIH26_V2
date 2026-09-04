"""Initial Schema Creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-02 23:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Patients Table
    op.create_table(
        'patients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('national_health_id', sa.String(length=100), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('dob', sa.String(length=20), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False),
        sa.Column('contact_number', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patients_national_health_id'), 'patients', ['national_health_id'], unique=True)

    # 2. Sessions Table
    op.create_table(
        'sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_section', sa.String(length=50), nullable=False),
        sa.Column('session_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_status'), 'sessions', ['status'], unique=False)

    # 3. Conversation Turns Table
    op.create_table(
        'conversation_turns',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('turn_index', sa.Integer(), nullable=False),
        sa.Column('speaker', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('extracted_data', sa.JSON(), nullable=False),
        sa.Column('safety_alerts', sa.JSON(), nullable=False),
        sa.Column('section', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_turns_session_id'), 'conversation_turns', ['session_id'], unique=False)

    # 4. Documents Table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_session_id'), 'documents', ['session_id'], unique=False)

    # 5. Extracted Entities Table
    op.create_table(
        'extracted_entities',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_name', sa.String(length=200), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('numeric_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('reference_range', sa.String(length=100), nullable=True),
        sa.Column('is_abnormal', sa.Boolean(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_extracted_entities_document_id'), 'extracted_entities', ['document_id'], unique=False)
    op.create_index(op.f('ix_extracted_entities_session_id'), 'extracted_entities', ['session_id'], unique=False)

    # 6. Summaries Table
    op.create_table(
        'summaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('hpi', sa.Text(), nullable=True),
        sa.Column('pmh', sa.Text(), nullable=True),
        sa.Column('drug_and_allergy', sa.Text(), nullable=True),
        sa.Column('family_history', sa.Text(), nullable=True),
        sa.Column('personal_history', sa.Text(), nullable=True),
        sa.Column('ros', sa.Text(), nullable=True),
        sa.Column('prior_investigations', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('physician_notes', sa.Text(), nullable=True),
        sa.Column('llm_model', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_summaries_session_id'), 'summaries', ['session_id'], unique=False)

    # 7. Consents Table
    op.create_table(
        'consents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('purpose', sa.String(length=255), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('terms_version', sa.String(length=50), nullable=False),
        sa.Column('signature_hash', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consents_patient_id'), 'consents', ['patient_id'], unique=False)
    op.create_index(op.f('ix_consents_session_id'), 'consents', ['session_id'], unique=False)

    # 8. Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_session_id'), 'audit_logs', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('consents')
    op.drop_table('summaries')
    op.drop_table('extracted_entities')
    op.drop_table('documents')
    op.drop_table('conversation_turns')
    op.drop_table('sessions')
    op.drop_table('patients')
