"""add clerk_id to users and candidates

Revision ID: a1b2c3d4e5f6
Revises: 4e7e100fb216
Create Date: 2026-05-14 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4e7e100fb216'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('clerk_id', sa.String(255), nullable=True, index=True))
    op.add_column('candidates', sa.Column('clerk_id', sa.String(255), nullable=True, index=True))


def downgrade() -> None:
    op.drop_column('users', 'clerk_id')
    op.drop_column('candidates', 'clerk_id')
