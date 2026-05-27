"""add candidate evaluation fields

Revision ID: 7a9b8c6d5e4f
Revises: 4e7e100fb216
Create Date: 2026-05-22 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from typing import Union, Sequence


# revision identifiers, used by Alembic.
revision: str = '7a9b8c6d5e4f'
down_revision: Union[str, None] = '4e7e100fb216'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add numeric evaluation columns with sensible defaults
    op.add_column('candidates', sa.Column('screening_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'))
    op.add_column('candidates', sa.Column('mcq_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'))
    op.add_column('candidates', sa.Column('coding_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'))
    op.add_column('candidates', sa.Column('risk_penalty', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'))
    op.add_column('candidates', sa.Column('composite_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'))
    op.add_column('candidates', sa.Column('adjusted_final_score', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.0'))

    # Recommendation and HR decision/audit fields
    op.add_column('candidates', sa.Column('recommendation', sa.String(length=30), nullable=True))
    op.add_column('candidates', sa.Column('decision_reason', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('decision_by', sa.String(length=36), nullable=True))
    op.add_column('candidates', sa.Column('decision_timestamp', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('candidates', 'decision_timestamp')
    op.drop_column('candidates', 'decision_by')
    op.drop_column('candidates', 'decision_reason')
    op.drop_column('candidates', 'recommendation')
    op.drop_column('candidates', 'adjusted_final_score')
    op.drop_column('candidates', 'composite_score')
    op.drop_column('candidates', 'risk_penalty')
    op.drop_column('candidates', 'coding_score')
    op.drop_column('candidates', 'mcq_score')
    op.drop_column('candidates', 'screening_score')
