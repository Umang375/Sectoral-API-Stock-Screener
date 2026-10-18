"""add return_2y to stocks

Revision ID: 0003_add_return_2y_to_stocks
Revises: 0002_add_ohlc_to_daily_snapshots
Create Date: 2026-10-18 21:38:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_return_2y_to_stocks'
down_revision: Union[str, None] = '0002_add_ohlc_to_daily_snapshots'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE stocks ADD COLUMN IF NOT EXISTS return_2y DOUBLE PRECISION;")


def downgrade() -> None:
    op.drop_column('stocks', 'return_2y')
