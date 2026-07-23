"""Stock and DailySnapshot models.

Design decisions:
─────────────────
Stock is the MASTER entity — one row per unique NSE/BSE symbol.
DailySnapshot is a FACT table — one row per stock × screener × market day.

WHY separate Stock from DailySnapshot?
- Stock holds slow-changing data (name, sector, first_seen).
- DailySnapshot holds fast-changing data (LTP, volume) that arrives daily.
- Normalisation: without it, we'd duplicate "Reliance Industries" 250+ times/year.

WHY raw_data as JSONB?
- Chartlink's response may include extra fields we don't model yet (MACD, RSI, etc.).
- Storing the raw JSON means we can mine those fields later without re-scraping.
- PostgreSQL JSONB is indexed and queryable — not just a blob.

WHY UniqueConstraint on (stock_id, screener_id, snapshot_date)?
- Prevents duplicate snapshots if the daily cron runs twice by mistake.
- Acts as a natural "upsert" boundary.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Stock(SQLModel, table=True):
    """Master stock record — one row per unique equity symbol."""

    __tablename__ = "stocks"

    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="NSE/BSE symbol, e.g. 'RELIANCE'",
    )
    name: str = Field(max_length=255, description="Company name")
    sector: str | None = Field(
        default=None,
        max_length=100,
        description="Broad sector from Chartlink (if available)",
    )
    first_seen: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this stock first appeared in any screener",
    )


class DailySnapshot(SQLModel, table=True):
    """Point-in-time market data for a stock on a given day and screener.

    One row = one stock's data from one screener run on one market day.
    """

    __tablename__ = "daily_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "screener_id",
            "snapshot_date",
            name="uq_snapshot_stock_screener_date",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)
    screener_id: int = Field(foreign_key="screeners.id", index=True)

    ltp: float = Field(description="Last Traded Price")
    volume: int | None = Field(default=None, description="Trading volume")
    change_pct: float | None = Field(
        default=None, description="Daily change percentage"
    )
    snapshot_date: date = Field(index=True, description="Market date")

    # Store the full Chartlink response for future mining.
    # sa_column is used because SQLModel doesn't natively support JSONB.
    raw_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
