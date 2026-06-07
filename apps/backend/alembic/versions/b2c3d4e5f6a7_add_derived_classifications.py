"""add derived_classifications

Revision ID: b2c3d4e5f6a7
Revises: aa60cfa62c90
Create Date: 2026-06-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'aa60cfa62c90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the derived_classifications table
    op.create_table(
        'derived_classifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.String(length=255), nullable=False),
        sa.Column('encounter_id', sa.String(length=255), nullable=False),
        sa.Column('axis', sa.Enum('A', 'B', 'C', 'E', name='axistype'), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('source_engine', sa.String(length=100), nullable=False),
        sa.Column('rule_version_semantic', sa.String(length=50), nullable=False),
        sa.Column('engine_hash', sa.String(length=128), nullable=False),
        sa.Column('completeness_status', sa.Enum('complete', 'partial', 'indeterminate', name='completenessstatus'), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Indexes
    op.create_index(op.f('ix_derived_classifications_patient_id'), 'derived_classifications', ['patient_id'], unique=False)
    op.create_index(op.f('ix_derived_classifications_encounter_id'), 'derived_classifications', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_derived_classifications_axis'), 'derived_classifications', ['axis'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_derived_classifications_axis'), table_name='derived_classifications')
    op.drop_index(op.f('ix_derived_classifications_encounter_id'), table_name='derived_classifications')
    op.drop_index(op.f('ix_derived_classifications_patient_id'), table_name='derived_classifications')
    op.drop_table('derived_classifications')
    
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE axistype')
        op.execute('DROP TYPE completenessstatus')
