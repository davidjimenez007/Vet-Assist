"""Add client_otps table for OTP authentication

Revision ID: 002
Revises: 001
Create Date: 2024-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: metadata column rename may have already been done manually
    # Skip if column doesn't exist or already renamed

    # Create client_otps table
    op.create_table(
        'client_otps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0'),
        sa.Column('verified', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['clinic_id'], ['clinics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for phone lookups
    op.create_index('idx_client_otps_phone_clinic', 'client_otps', ['phone', 'clinic_id'])

    # Note: password_hash column may already exist in staff table from previous setup
    # Using try/except to handle case where column already exists
    try:
        op.add_column('staff', sa.Column('password_hash', sa.String(length=255), nullable=True))
    except Exception:
        pass  # Column already exists


def downgrade() -> None:
    try:
        op.drop_column('staff', 'password_hash')
    except Exception:
        pass
    op.drop_index('idx_client_otps_phone_clinic')
    op.drop_table('client_otps')
