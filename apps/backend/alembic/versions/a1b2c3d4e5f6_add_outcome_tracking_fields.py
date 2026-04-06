"""add outcome tracking fields to encounters

Revision ID: a1b2c3d4e5f6
Revises: c032f4bc73dc
Create Date: 2026-04-06

Research dataset quality fix: without outcome fields, the dataset can only
describe clinical states (inputs + motor outputs), not validate whether
interventions worked. These 5 columns enable longitudinal outcome research.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c032f4bc73dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "encounters",
        sa.Column("weight_current_kg", sa.Float(), nullable=True),
    )
    op.add_column(
        "encounters",
        sa.Column("outcome_status", sa.String(20), nullable=True),
    )
    op.add_column(
        "encounters",
        sa.Column("adverse_event", sa.String(500), nullable=True),
    )
    op.add_column(
        "encounters",
        sa.Column("medication_changed", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "encounters",
        sa.Column("adherence_reported", sa.String(10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("encounters", "adherence_reported")
    op.drop_column("encounters", "medication_changed")
    op.drop_column("encounters", "adverse_event")
    op.drop_column("encounters", "outcome_status")
    op.drop_column("encounters", "weight_current_kg")
