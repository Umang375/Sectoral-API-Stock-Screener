"""CLI tool to backfill 2-year price history for stocks in the database.

Usage:
    python -m app.scripts.backfill_history [--dry-run] [--limit 20] [--range 2y]
"""

import argparse
import asyncio
import logging
import sys

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import async_session_factory
from app.models.screener import Screener
from app.models.stock import DailySnapshot, Stock
from app.services.history_fetcher import HistoryFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backfill_history")


async def run_history_backfill(
    min_snapshots: int = 10,
    limit: int | None = None,
    dry_run: bool = False,
    range_str: str = "2y",
) -> None:
    """Identify stocks lacking historical snapshots and backfill their 2-year history."""
    fetcher = HistoryFetcher()

    async with async_session_factory() as session:
        # Default screener for provenance
        screener_stmt = select(Screener).limit(1)
        screener_res = await session.exec(screener_stmt)
        screener = screener_res.first()
        screener_id = screener.id if screener else 1

        # Query all stocks with their current snapshot count
        stmt = select(Stock).order_by(Stock.id)
        result = await session.exec(stmt)
        all_stocks = list(result.all())

        if not all_stocks:
            logger.info("No stocks found in the database. Exiting.")
            return

        # Check snapshot counts
        stocks_to_backfill: list[Stock] = []
        for stock in all_stocks:
            cnt_stmt = select(func.count(DailySnapshot.id)).where(
                DailySnapshot.stock_id == stock.id
            )
            count = (await session.exec(cnt_stmt)).one()
            if count < min_snapshots:
                stocks_to_backfill.append(stock)

        if limit:
            stocks_to_backfill = stocks_to_backfill[:limit]

        logger.info(
            "Found %d total stocks. Targets needing historical backfill: %d (threshold < %d, dry_run=%s)",
            len(all_stocks),
            len(stocks_to_backfill),
            min_snapshots,
            dry_run,
        )

        if not stocks_to_backfill:
            logger.info("All stocks already have historical snapshots. Nothing to do.")
            return

        if dry_run:
            logger.info("Dry run preview of stocks to backfill:")
            for s in stocks_to_backfill:
                logger.info("  - %s: %s", s.symbol, s.name)
            return

        # Execute backfill
        total_points_added = 0
        success_count = 0

        for i, stock in enumerate(stocks_to_backfill, start=1):
            logger.info(
                "[%d/%d] Backfilling %s (%s)...",
                i,
                len(stocks_to_backfill),
                stock.symbol,
                stock.name,
            )
            try:
                added = await fetcher.backfill_stock(
                    stock_id=stock.id,
                    symbol=stock.symbol,
                    screener_id=screener_id,
                    session=session,
                    range_str=range_str,
                )
                if added > 0:
                    total_points_added += added
                    success_count += 1
                # Polite short pause between Yahoo requests
                await asyncio.sleep(0.3)
            except Exception:
                logger.exception("Failed to backfill history for %s", stock.symbol)

        logger.info(
            "Completed! Backfilled %d/%d stocks. Total historical snapshots added: %d",
            success_count,
            len(stocks_to_backfill),
            total_points_added,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill 2-year price history for stocks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview stocks to backfill without writing to DB",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of stocks to process",
    )
    parser.add_argument(
        "--min-snapshots",
        type=int,
        default=10,
        help="Snapshot threshold to trigger backfill (default: 10)",
    )
    parser.add_argument(
        "--range",
        type=str,
        default="2y",
        help="Yahoo Finance history range (default: '2y')",
    )
    args = parser.parse_args()

    asyncio.run(
        run_history_backfill(
            min_snapshots=args.min_snapshots,
            limit=args.limit,
            dry_run=args.dry_run,
            range_str=args.range,
        )
    )


if __name__ == "__main__":
    main()
