"""Add WhatsApp automation tables (emergencies, follow-ups, conversation state)

Revision ID: 003
Revises: 002
Create Date: 2024-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================
    # Update conversations table with state machine fields
    # ==========================================

    op.add_column('conversations', sa.Column('client_phone', sa.String(length=20), nullable=True))
    op.add_column('conversations', sa.Column('conversation_type', sa.String(length=20), server_default='inbound'))
    op.add_column('conversations', sa.Column('state', sa.String(length=50), server_default='GREETING'))
    op.add_column('conversations', sa.Column('state_data', postgresql.JSONB(), server_default='{}'))
    op.add_column('conversations', sa.Column('last_state_change', sa.DateTime(timezone=True), nullable=True))
    op.add_column('conversations', sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('conversations', sa.Column('extracted_pet_name', sa.String(length=100), nullable=True))
    op.add_column('conversations', sa.Column('extracted_pet_species', sa.String(length=50), nullable=True))
    op.add_column('conversations', sa.Column('extracted_client_name', sa.String(length=255), nullable=True))
    op.add_column('conversations', sa.Column('extracted_reason', sa.Text(), nullable=True))
    op.add_column('conversations', sa.Column('emergency_keywords', postgresql.ARRAY(sa.String()), server_default='{}'))
    op.add_column('conversations', sa.Column('emergency_description', sa.Text(), nullable=True))
    op.add_column('conversations', sa.Column('offered_slots', postgresql.JSONB(), server_default='{}'))

    # Create indexes for conversation queries
    op.create_index('idx_conversations_state', 'conversations', ['clinic_id', 'state'])
    op.create_index('idx_conversations_timeout', 'conversations', ['timeout_at'], postgresql_where=sa.text("state != 'CLOSED'"))
    op.create_index('idx_conversations_phone', 'conversations', ['clinic_id', 'client_phone'])

    # ==========================================
    # Update clients table with emergency tracking
    # ==========================================

    op.add_column('clients', sa.Column('false_emergency_count', sa.Integer(), server_default='0'))
    op.add_column('clients', sa.Column('emergency_access_revoked', sa.Boolean(), server_default='false'))

    # ==========================================
    # Update appointments table with priority and follow-up
    # ==========================================

    op.add_column('appointments', sa.Column('priority', sa.String(length=20), server_default='normal'))
    op.add_column('appointments', sa.Column('emergency_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('appointments', sa.Column('follow_up_protocol', sa.String(length=50), nullable=True))

    # ==========================================
    # Create emergency_events table
    # ==========================================

    op.create_table(
        'emergency_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_phone', sa.String(length=20), nullable=False),
        sa.Column('pet_name', sa.String(length=100), nullable=True),
        sa.Column('pet_species', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords_detected', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('priority', sa.String(length=20), server_default='high'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['staff.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['staff.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_emergency_events_active', 'emergency_events', ['clinic_id', 'status'], postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_emergency_events_clinic', 'emergency_events', ['clinic_id', 'created_at'])

    # ==========================================
    # Create emergency_alerts table
    # ==========================================

    op.create_table(
        'emergency_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('emergency_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_phone', sa.String(length=20), nullable=False),
        sa.Column('contact_name', sa.String(length=100), nullable=True),
        sa.Column('contact_role', sa.String(length=50), nullable=True),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['emergency_id'], ['emergency_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ==========================================
    # Create follow_up_protocols table
    # ==========================================

    op.create_table(
        'follow_up_protocols',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('procedure_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('schedule_hours', postgresql.ARRAY(sa.Integer()), server_default='{}'),
        sa.Column('message_templates', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('escalation_keywords', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_follow_up_protocols_clinic', 'follow_up_protocols', ['clinic_id', 'procedure_type'])

    # ==========================================
    # Create follow_ups table
    # ==========================================

    op.create_table(
        'follow_ups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pet_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('protocol_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_template', sa.Text(), nullable=False),
        sa.Column('escalation_keywords', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('sequence_number', sa.Integer(), server_default='1'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id']),
        sa.ForeignKeyConstraint(['protocol_id'], ['follow_up_protocols.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_follow_ups_pending', 'follow_ups', ['scheduled_at'], postgresql_where=sa.text("status = 'pending'"))
    op.create_index('idx_follow_ups_clinic', 'follow_ups', ['clinic_id', 'status'])

    # ==========================================
    # Create follow_up_responses table
    # ==========================================

    op.create_table(
        'follow_up_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('follow_up_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('analysis_result', postgresql.JSONB(), server_default='{}'),
        sa.Column('matched_keywords', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('requires_escalation', sa.Boolean(), server_default='false'),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['follow_up_id'], ['follow_ups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('follow_up_responses')
    op.drop_table('follow_ups')
    op.drop_table('follow_up_protocols')
    op.drop_table('emergency_alerts')
    op.drop_table('emergency_events')

    # Remove added columns from appointments
    op.drop_column('appointments', 'follow_up_protocol')
    op.drop_column('appointments', 'emergency_id')
    op.drop_column('appointments', 'priority')

    # Remove added columns from clients
    op.drop_column('clients', 'emergency_access_revoked')
    op.drop_column('clients', 'false_emergency_count')

    # Remove added columns and indexes from conversations
    op.drop_index('idx_conversations_phone')
    op.drop_index('idx_conversations_timeout')
    op.drop_index('idx_conversations_state')
    op.drop_column('conversations', 'offered_slots')
    op.drop_column('conversations', 'emergency_description')
    op.drop_column('conversations', 'emergency_keywords')
    op.drop_column('conversations', 'extracted_reason')
    op.drop_column('conversations', 'extracted_client_name')
    op.drop_column('conversations', 'extracted_pet_species')
    op.drop_column('conversations', 'extracted_pet_name')
    op.drop_column('conversations', 'timeout_at')
    op.drop_column('conversations', 'last_state_change')
    op.drop_column('conversations', 'state_data')
    op.drop_column('conversations', 'state')
    op.drop_column('conversations', 'conversation_type')
    op.drop_column('conversations', 'client_phone')
