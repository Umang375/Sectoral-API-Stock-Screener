"""Weekly returns calculator for stocks and tag cohorts.

PATTERN: Batch Processor
────────────────────────
This service runs as a scheduled batch job (Monday 7 AM), not on user requests.
It reads raw data (daily_snapshots), computes derived data (weekly_returns,
tag_weekly_returns), and writes the results back.

This is the MATERIALISED VIEW pattern implemented manually:
- Compute once → serve thousands of reads.
- Without this, every /api/tags/{label}/returns request would need a
  multi-table JOIN + GROUP BY + AVG/MEDIAN — expensive under 1000 concurrent users.

WHY manual materialisation instead of Postgres MATERIALIZED VIEW?
1. We need historical rows (one per week), not just the latest snapshot.
2. We want to track stock_count, both avg AND median — hard in a single SQL view.
3. It's more portable — no Postgres-specific DDL.

FORMULA:
  return_pct = ((close_ltp - open_ltp) / open_ltp) × 100

  open_ltp  = LTP from the EARLIEST snapshot in the week
  close_ltp = LTP from the LATEST snapshot in the week
"""

import logging
from datetime import date, timedelta
from statistics import mean, median

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.returns import TagWeeklyReturns, WeeklyReturns
from app.models.stock import DailySnapshot, Stock
from app.models.tag import StockTag, Tag

logger = logging.getLogger(__name__)


class ReturnsCalculator:
    """Computes and stores weekly returns for stocks and tag cohorts.

    Usage:
        calculator = ReturnsCalculator()
        summary = await calculator.calculate_all(session)
        # summary = {"stocks_processed": 342, "tags_processed": 87}
    """

    async def calculate_all(
        self,
        session: AsyncSession,
        target_date: date | None = None,
    ) -> dict[str, int]:
        """Run the full weekly returns pipeline.

        Args:
            session: Async database session.
            target_date: Compute returns for the week ending on/before this date.
                         Defaults to today (typically called on Monday for last week).

        Returns:
            Summary dict with counts of stocks and tags processed.
        """
        today = target_date or date.today()
        week_start, week_end = self._get_last_trading_week(today)

        logger.info(
            "Calculating weekly returns for %s to %s",
            week_start.isoformat(),
            week_end.isoformat(),
        )

        stocks_count = await self._calculate_stock_returns(session, week_start, week_end)
        tags_count = await self._calculate_tag_returns(session, week_start, week_end)

        await session.commit()

        logger.info(
            "Weekly returns complete: %d stocks, %d tags processed",
            stocks_count,
            tags_count,
        )
        return {"stocks_processed": stocks_count, "tags_processed": tags_count}

    # ── Per-stock returns ────────────────────────────────────────────────

    async def _calculate_stock_returns(
        self,
        session: AsyncSession,
        week_start: date,
        week_end: date,
    ) -> int:
        """Compute weekly return for every stock that has snapshots in the range.

        For each stock:
        1. Find the earliest snapshot (open_ltp) in the week.
        2. Find the latest snapshot (close_ltp) in the week.
        3. return_pct = ((close - open) / open) × 100
        4. Upsert into weekly_returns table.
        """
        # Get all stocks that have at least one snapshot in the date range.
        stmt = (
            select(DailySnapshot.stock_id)
            .where(
                DailySnapshot.snapshot_date >= week_start,
                DailySnapshot.snapshot_date <= week_end,
            )
            .distinct()
        )
        result = await session.exec(stmt)
        stock_ids = list(result.all())

        processed = 0
        for stock_id in stock_ids:
            # Earliest snapshot in the week = "open"
            open_stmt = (
                select(DailySnapshot.ltp)
                .where(
                    DailySnapshot.stock_id == stock_id,
                    DailySnapshot.snapshot_date >= week_start,
                    DailySnapshot.snapshot_date <= week_end,
                )
                .order_by(DailySnapshot.snapshot_date.asc())
                .limit(1)
            )
            open_result = await session.exec(open_stmt)
            open_ltp = open_result.first()

            # Latest snapshot in the week = "close"
            close_stmt = (
                select(DailySnapshot.ltp)
                .where(
                    DailySnapshot.stock_id == stock_id,
                    DailySnapshot.snapshot_date >= week_start,
                    DailySnapshot.snapshot_date <= week_end,
                )
                .order_by(DailySnapshot.snapshot_date.desc())
                .limit(1)
            )
            close_result = await session.exec(close_stmt)
            close_ltp = close_result.first()

            if open_ltp and close_ltp and open_ltp > 0:
                return_pct = round(((close_ltp - open_ltp) / open_ltp) * 100, 4)

                # Upsert: check if we already computed returns for this stock+week.
                existing_stmt = select(WeeklyReturns).where(
                    WeeklyReturns.stock_id == stock_id,
                    WeeklyReturns.week_start == week_start,
                )
                existing_result = await session.exec(existing_stmt)
                existing = existing_result.first()

                if existing:
                    existing.open_ltp = open_ltp
                    existing.close_ltp = close_ltp
                    existing.return_pct = return_pct
                    session.add(existing)
                else:
                    session.add(
                        WeeklyReturns(
                            stock_id=stock_id,
                            open_ltp=open_ltp,
                            close_ltp=close_ltp,
                            return_pct=return_pct,
                            week_start=week_start,
                            week_end=week_end,
                        )
                    )
                processed += 1

        return processed

    # ── Per-tag aggregated returns ───────────────────────────────────────

    async def _calculate_tag_returns(
        self,
        session: AsyncSession,
        week_start: date,
        week_end: date,
    ) -> int:
        """Aggregate weekly returns by tag.

        For each tag:
        1. Find all stocks linked to that tag.
        2. Get their weekly returns (computed above).
        3. Calculate avg and median return_pct.
        4. Upsert into tag_weekly_returns table.

        WHY both avg AND median?
        - One stock with +50% return skews the average.
        - Median gives the "typical" stock performance in that sector.
        """
        # Get all tags that have at least one stock.
        stmt = select(Tag)
        result = await session.exec(stmt)
        all_tags = list(result.all())

        processed = 0
        for tag in all_tags:
            # Get stock IDs linked to this tag.
            stock_ids_stmt = select(StockTag.stock_id).where(StockTag.tag_id == tag.id)
            stock_ids_result = await session.exec(stock_ids_stmt)
            stock_ids = list(stock_ids_result.all())

            if not stock_ids:
                continue

            # Get weekly returns for those stocks.
            returns_stmt = select(WeeklyReturns.return_pct).where(
                WeeklyReturns.stock_id.in_(stock_ids),
                WeeklyReturns.week_start == week_start,
            )
            returns_result = await session.exec(returns_stmt)
            return_values = list(returns_result.all())

            if not return_values:
                continue

            avg_ret = round(mean(return_values), 4)
            med_ret = round(median(return_values), 4)

            # Upsert tag weekly returns.
            existing_stmt = select(TagWeeklyReturns).where(
                TagWeeklyReturns.tag_id == tag.id,
                TagWeeklyReturns.week_start == week_start,
            )
            existing_result = await session.exec(existing_stmt)
            existing = existing_result.first()

            if existing:
                existing.avg_return_pct = avg_ret
                existing.median_return_pct = med_ret
                existing.stock_count = len(return_values)
                session.add(existing)
            else:
                session.add(
                    TagWeeklyReturns(
                        tag_id=tag.id,
                        avg_return_pct=avg_ret,
                        median_return_pct=med_ret,
                        stock_count=len(return_values),
                        week_start=week_start,
                        week_end=week_end,
                    )
                )
            processed += 1

        return processed

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _get_last_trading_week(reference: date) -> tuple[date, date]:
        """Get the Monday-to-Friday range of the most recent complete trading week.

        If called on Monday, returns last week's Mon-Fri.
        If called on Wednesday, also returns last week's Mon-Fri
        (we only compute complete weeks).
        """
        # Find last Friday (or today if it is Friday).
        days_since_friday = (reference.weekday() - 4) % 7
        if days_since_friday == 0 and reference.weekday() != 4:
            days_since_friday = 7
        week_end = reference - timedelta(days=days_since_friday)

        # Monday of that same week.
        week_start = week_end - timedelta(days=4)

        return week_start, week_end
