"""add is_banned to users

Revision ID: 6933c81675bf
Revises: 945f0e085f49
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '6933c81675bf'
down_revision: Union[str, Sequence[str], None] = '945f0e085f49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('is_banned', sa.Integer(), nullable=False, server_default='0'))

def downgrade() -> None:
    op.drop_column('users', 'is_banned')
