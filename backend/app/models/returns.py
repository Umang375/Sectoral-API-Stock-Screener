"""Weekly returns models — pre-computed performance data.

Design decisions:
─────────────────
WHY pre-computed tables instead of computing on-the-fly?
- With 1000 users reading /api/tags/{label}/returns, computing
  "average return of all stocks tagged 'auto ancillaries' last week"
  on every request would hammer the DB with JOINs + aggregations.
- Pre-computing once (Monday 7 AM cron) and storing the result means
  reads are simple SELECT lookups — O(1) regardless of user count.
- This is the MATERIALISED VIEW pattern, done manually so we can
  track history (each week gets its own row, building a time series).

WHY both avg_return_pct AND median_return_pct for tags?
- Mean is skewed by outliers (one stock +50% drags the average up).
- Median gives a better "typical" stock performance in that sector.
- Reporting both lets the frontend/user choose which matters.
"""

from datetime import date

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class TagDailyReturns(SQLModel, table=True):
    """End-of-day aggregate return for all stocks carrying a tag."""

    __tablename__ = "tag_daily_returns"
    __table_args__ = (
        UniqueConstraint("tag_id", "snapshot_date", name="uq_tag_daily_return"),
    )

    id: int | None = Field(default=None, primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", index=True)
    snapshot_date: date = Field(index=True)
    avg_return_pct: float
    median_return_pct: float
    stock_count: int
    advancing_count: int
    declining_count: int


class WeeklyReturns(SQLModel, table=True):
    """Pre-computed weekly return for a single stock.

    One row = one stock's performance over one Mon-Fri trading week.
    """

    __tablename__ = "weekly_returns"

    id: int | None = Field(default=None, primary_key=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)

    open_ltp: float = Field(description="LTP at week start (Monday / first trading day)")
    close_ltp: float = Field(description="LTP at week end (Friday / last trading day)")
    return_pct: float = Field(
        description="((close - open) / open) × 100"
    )

    week_start: date = Field(index=True, description="Monday of the week")
    week_end: date = Field(description="Friday of the week")


class TagWeeklyReturns(SQLModel, table=True):
    """Aggregated weekly return across all stocks sharing a tag.

    One row = one tag cohort's aggregate performance for one week.
    """

    __tablename__ = "tag_weekly_returns"

    id: int | None = Field(default=None, primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", index=True)

    avg_return_pct: float = Field(description="Mean return across stocks with this tag")
    median_return_pct: float = Field(description="Median return (robust to outliers)")
    stock_count: int = Field(description="Number of stocks in this cohort")

    week_start: date = Field(index=True, description="Monday of the week")
    week_end: date = Field(description="Friday of the week")
