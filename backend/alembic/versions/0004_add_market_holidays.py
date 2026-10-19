"""add market_holidays table

Revision ID: 0004_add_market_holidays
Revises: 0003_add_return_2y_to_stocks
Create Date: 2026-10-19 12:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_add_market_holidays'
down_revision: Union[str, None] = '0003_add_return_2y_to_stocks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS market_holidays (
            id SERIAL PRIMARY KEY,
            holiday_date DATE NOT NULL UNIQUE,
            description VARCHAR NOT NULL,
            holiday_type VARCHAR NOT NULL DEFAULT 'TRADING_HOLIDAY',
            closed_exchanges VARCHAR NOT NULL DEFAULT 'NSE,BSE',
            year INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_market_holidays_holiday_date ON market_holidays (holiday_date);
        CREATE INDEX IF NOT EXISTS ix_market_holidays_year ON market_holidays (year);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS market_holidays;")
