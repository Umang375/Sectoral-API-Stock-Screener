"""add stock is_active and last_activated_at

Revision ID: 0001_add_stock_soft_delete
Revises: 
Create Date: 2026-10-17 23:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_add_stock_soft_delete'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'stocks',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        'ix_stocks_is_active',
        'stocks',
        ['is_active'],
        unique=False,
    )
    op.add_column(
        'stocks',
        sa.Column('last_activated_at', sa.Date(), nullable=False, server_default=sa.func.current_date()),
    )


def downgrade() -> None:
    op.drop_column('stocks', 'last_activated_at')
    op.drop_index('ix_stocks_is_active', table_name='stocks')
    op.drop_column('stocks', 'is_active')
