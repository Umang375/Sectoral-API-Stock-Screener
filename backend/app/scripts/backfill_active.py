"""Script to backfill 1-year Yahoo Finance historical snapshots for all active stocks.

Usage:
    .\\venv\\Scripts\\python.exe -m app.scripts.backfill_active
"""

import asyncio
import logging
import sys
import time

from sqlmodel import select, func

from app.database import async_session_factory
from app.models.stock import Stock, DailySnapshot
from app.services.history_fetcher import HistoryFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backfill_active")


async def backfill_all_active_stocks(range_str: str = "2y", max_concurrent: int = 5):
    """Backfill 1-year history and 2Y return for all stocks where is_active == True."""
    start_time = time.time()

    async with async_session_factory() as session:
        # Query all active stocks
        stmt = select(Stock).where(Stock.is_active == True).order_by(Stock.symbol)
        result = await session.exec(stmt)
        stocks = list(result.all())

    total_stocks = len(stocks)
    logger.info("Found %d active stocks to backfill with %s history", total_stocks, range_str)

    fetcher = HistoryFetcher(timeout=20.0)
    sem = asyncio.Semaphore(max_concurrent)

    success_count = 0
    skipped_count = 0
    fail_count = 0

    async def process_stock(idx: int, stock_id: int, symbol: str):
        nonlocal success_count, skipped_count, fail_count
        async with sem:
            async with async_session_factory() as local_session:
                try:
                    # Check how many snapshots this stock already has with OHLC
                    cnt_stmt = select(func.count(DailySnapshot.id)).where(
                        DailySnapshot.stock_id == stock_id,
                        DailySnapshot.open.is_not(None),
                        DailySnapshot.high != DailySnapshot.low,
                    )
                    count_res = await local_session.exec(cnt_stmt)
                    ohlc_count = count_res.one()

                    stock_obj = await local_session.get(Stock, stock_id)
                    # If already has >= 200 genuine OHLC snapshots AND return_2y is present, skip
                    if ohlc_count >= 200 and stock_obj and stock_obj.return_2y is not None:
                        skipped_count += 1
                        logger.info(
                            "[%d/%d] %s: Skipped (already has %d OHLC snapshots & 2Y return)",
                            idx,
                            total_stocks,
                            symbol,
                            ohlc_count,
                        )
                        return

                    # Backfill 1 year of history
                    count = await fetcher.backfill_stock(
                        stock_id=stock_id,
                        symbol=symbol,
                        screener_id=1,
                        session=local_session,
                        range_str=range_str,
                    )
                    success_count += 1
                    logger.info(
                        "[%d/%d] %s: Backfilled %d snapshots",
                        idx,
                        total_stocks,
                        symbol,
                        count,
                    )
                except Exception as e:
                    fail_count += 1
                    logger.warning(
                        "[%d/%d] %s: Backfill failed: %s",
                        idx,
                        total_stocks,
                        symbol,
                        e,
                    )
            # Brief delay to be polite to Yahoo Finance API
            await asyncio.sleep(0.08)

    # Run in parallel batches of 15
    batch_size = 15
    for i in range(0, total_stocks, batch_size):
        batch = stocks[i : i + batch_size]
        tasks = [
            process_stock(i + j + 1, s.id, s.symbol)
            for j, s in enumerate(batch)
        ]
        await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    logger.info(
        "Finished backfill in %.1f seconds: %d backfilled, %d skipped, %d failed out of %d active stocks",
        elapsed,
        success_count,
        skipped_count,
        fail_count,
        total_stocks,
    )


if __name__ == "__main__":
    asyncio.run(backfill_all_active_stocks("2y"))
