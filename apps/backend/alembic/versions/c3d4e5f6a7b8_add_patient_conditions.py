"""add patient_conditions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-07 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the patient_conditions table
    op.create_table(
        'patient_conditions',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('patient_id', sa.String(length=255), nullable=False),
        sa.Column('onset_encounter_id', sa.String(length=255), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('system', sa.String(length=50), nullable=False, server_default='CIE-10'),
        sa.Column('status', sa.Enum('active', 'resolved', 'in_remission', name='conditionstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['onset_encounter_id'], ['encounters.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Indexes
    op.create_index(op.f('ix_patient_conditions_patient_id'), 'patient_conditions', ['patient_id'], unique=False)
    op.create_index(op.f('ix_patient_conditions_onset_encounter_id'), 'patient_conditions', ['onset_encounter_id'], unique=False)
    op.create_index(op.f('ix_patient_conditions_code'), 'patient_conditions', ['code'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_patient_conditions_code'), table_name='patient_conditions')
    op.drop_index(op.f('ix_patient_conditions_onset_encounter_id'), table_name='patient_conditions')
    op.drop_index(op.f('ix_patient_conditions_patient_id'), table_name='patient_conditions')
    op.drop_table('patient_conditions')
    
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE conditionstatus')
