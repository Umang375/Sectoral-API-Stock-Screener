"""add ohlc columns to daily_snapshots

Revision ID: 0002_add_ohlc_to_daily_snapshots
Revises: 0001_add_stock_soft_delete
Create Date: 2026-10-18 21:15:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_add_ohlc_to_daily_snapshots'
down_revision: Union[str, None] = '0001_add_stock_soft_delete'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS open DOUBLE PRECISION;")
    op.execute("ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS high DOUBLE PRECISION;")
    op.execute("ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS low DOUBLE PRECISION;")
    op.execute("ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS close DOUBLE PRECISION;")


def downgrade() -> None:
    op.drop_column('daily_snapshots', 'close')
    op.drop_column('daily_snapshots', 'low')
    op.drop_column('daily_snapshots', 'high')
    op.drop_column('daily_snapshots', 'open')
