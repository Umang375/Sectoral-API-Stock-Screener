"""Backfill and reclassify stocks into the predefined sector taxonomy.

Usage:
    python -m app.scripts.backfill_sectors [--all] [--limit 50] [--dry-run]
"""

import argparse
import asyncio
import logging
import sys

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.constants.sectors import PREDEFINED_SECTORS
from app.database import async_session_factory
from app.models.screener import Screener
from app.models.stock import DailySnapshot, Stock
from app.redis_client import get_redis
from app.services.gemini_tagger import GeminiTagger
from app.utils.rate_limiter import RateLimiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backfill_sectors")


async def run_backfill(
    reclassify_all: bool = False,
    limit: int | None = None,
    dry_run: bool = False,
) -> None:
    """Run the backfill process for stocks."""
    settings = get_settings()
    redis = await get_redis()
    rate_limiter = RateLimiter(rpm=settings.GEMINI_RPM, rpd=settings.GEMINI_RPD)
    tagger = GeminiTagger(rate_limiter=rate_limiter, redis=redis)

    valid_sectors_set = set(PREDEFINED_SECTORS)

    async with async_session_factory() as session:
        # Get a default screener for provenance
        screener_stmt = select(Screener).limit(1)
        screener_res = await session.exec(screener_stmt)
        screener = screener_res.first()
        screener_id = screener.id if screener else 1
        screener_name = screener.name if screener else "Backfill"

        # Query stocks
        stmt = select(Stock).order_by(Stock.id)
        result = await session.exec(stmt)
        all_stocks = list(result.all())

        if reclassify_all:
            target_stocks = all_stocks
        else:
            target_stocks = [
                s for s in all_stocks
                if not s.sector or s.sector not in valid_sectors_set
            ]

        if limit:
            target_stocks = target_stocks[:limit]

        logger.info(
            "Found %d total stocks. Targets to classify: %d (all=%s, dry_run=%s)",
            len(all_stocks),
            len(target_stocks),
            reclassify_all,
            dry_run,
        )

        if not target_stocks:
            logger.info("No stocks need classification. Exiting.")
            return

        if dry_run:
            logger.info("Dry run requested. Stocks that would be classified:")
            for s in target_stocks:
                logger.info("  - %s (%s) [current sector: %s]", s.symbol, s.name, s.sector)
            return

        # Prepare stocks_info with latest snapshots
        stocks_info: list[tuple[Stock, float, float | None]] = []
        for stock in target_stocks:
            snap_stmt = (
                select(DailySnapshot)
                .where(DailySnapshot.stock_id == stock.id)
                .order_by(DailySnapshot.snapshot_date.desc())
                .limit(1)
            )
            snap_res = await session.exec(snap_stmt)
            latest_snap = snap_res.first()
            ltp = latest_snap.ltp if latest_snap else 0.0
            change_pct = latest_snap.change_pct if latest_snap else 0.0
            stocks_info.append((stock, ltp, change_pct))

        logger.info("Starting Gemini batch classification...")
        await tagger.generate_tags_batch(
            stocks_info=stocks_info,
            screener_name=screener_name,
            screener_id=screener_id,
            session=session,
        )

        await session.commit()
        logger.info("Successfully completed sector backfill for %d stocks.", len(target_stocks))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill stocks with predefined sectors")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Reclassify all stocks, even if already classified",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of stocks to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview stocks to be classified without making API calls",
    )
    args = parser.parse_args()

    asyncio.run(
        run_backfill(
            reclassify_all=args.all,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
