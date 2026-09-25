"""add stripe + idempotency fields

Revision ID: a1b2c3d4e5f6
Revises: 0e1225cda731
Create Date: 2026-09-25 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '6933c81675bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Orders: add Stripe + idempotency columns ──
    op.add_column('orders', sa.Column('currency', sa.String(length=3), nullable=False, server_default='myr'))
    op.add_column('orders', sa.Column('stripe_session_id', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('idempotency_key', sa.String(length=64), nullable=True))

    op.create_index('ix_orders_stripe_session_id', 'orders', ['stripe_session_id'])
    op.create_index('ix_orders_idempotency_key', 'orders', ['idempotency_key'], unique=True)

    # ── Idempotency records table ──
    op.create_table(
        'idempotency_records',
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('request_path', sa.String(length=255), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=False),
        sa.Column('response_body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade() -> None:
    op.drop_table('idempotency_records')

    op.drop_index('ix_orders_idempotency_key', table_name='orders')
    op.drop_index('ix_orders_stripe_session_id', table_name='orders')

    op.drop_column('orders', 'idempotency_key')
    op.drop_column('orders', 'stripe_payment_intent_id')
    op.drop_column('orders', 'stripe_session_id')
    op.drop_column('orders', 'currency')
