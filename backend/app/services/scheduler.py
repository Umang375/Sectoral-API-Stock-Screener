"""APScheduler job definitions for automated data pipeline.

PATTERN: Orchestrator
─────────────────────
The scheduler is the ORCHESTRATOR — it doesn't contain business logic itself.
Instead, it calls the right services at the right time:

  6:30 PM Mon-Fri → ChartlinkScraper → GeminiTagger (per stock)
  7:00 AM Monday  → ReturnsCalculator
  Midnight Sunday → Cleanup old snapshots

WHY APScheduler instead of system cron (crontab)?
- Runs IN-PROCESS with FastAPI — no external dependency to configure.
- Can be registered in the app's lifespan (startup/shutdown).
- Supports async job functions natively.
- Render free tier doesn't support system cron; APScheduler works anywhere.

WHY AsyncIOScheduler?
- Our jobs call async services (DB sessions, Redis, httpx).
  AsyncIOScheduler runs jobs on the same event loop as FastAPI.

CAVEAT: Render free tier spins down after 15 min of inactivity.
  Use an external pinger (cron-job.org) to keep the service awake.
"""

import asyncio
import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.database import async_session_factory
from app.models.screener import Screener
from app.models.stock import DailySnapshot, Stock
from app.redis_client import get_redis
from app.services.chartlink_scraper import ChartlinkScraper
from app.services.gemini_tagger import GeminiTagger
from app.services.history_fetcher import backfill_stocks_in_background
from app.services.market_calendar import is_trading_day, sync_market_holidays_from_upstox
from app.services.returns_calculator import ReturnsCalculator
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Module-level scheduler instance — started/stopped in main.py lifespan.
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def daily_screener_fetch() -> None:
    """Run all active screeners, save snapshots, and generate tags.

    Called Mon-Fri at 6:30 PM IST (after market close).

    Pipeline for each screener:
    1. Fetch stocks from Chartlink via POST simulation.
    2. Upsert each stock into the `stocks` table.
    3. Save a daily_snapshot for each stock.
    4. Generate (or retrieve cached) tags for each stock via Gemini.
    """
    today = date.today()
    if not is_trading_day(today):
        logger.info("Today (%s) is an NSE market holiday or weekend. Skipping daily screener fetch.", today)
        return

    settings = get_settings()
    scraper = ChartlinkScraper()
    redis = await get_redis()
    rate_limiter = RateLimiter(rpm=settings.GEMINI_RPM, rpd=settings.GEMINI_RPD)
    tagger = GeminiTagger(rate_limiter=rate_limiter, redis=redis)

    try:
        async with async_session_factory() as session:
            # Get all active screeners.
            stmt = select(Screener).where(Screener.is_active == True)  # noqa: E712
            result = await session.exec(stmt)
            screeners = list(result.all())

            if not screeners:
                logger.warning("No active screeners configured. Skipping fetch.")
                return

            for screener_row in screeners:
                logger.info("Running screener: %s", screener_row.name)
                try:
                    scraped_stocks = await scraper.run_screener(screener_row.scan_clause)
                except Exception:
                    logger.exception("Failed to run screener: %s", screener_row.name)
                    continue

                today = date.today()
                stocks_info = []
                new_stocks_info: list[tuple[int, str]] = []

                for scraped in scraped_stocks:
                    if not scraped.symbol:
                        continue

                    # ── Upsert Stock ─────────────────────────────────────
                    stock_stmt = select(Stock).where(Stock.symbol == scraped.symbol)
                    stock_result = await session.exec(stock_stmt)
                    stock = stock_result.first()

                    if not stock:
                        stock = Stock(
                            symbol=scraped.symbol,
                            name=scraped.name,
                            is_active=True,
                            last_activated_at=today,
                        )
                        session.add(stock)
                        await session.flush()  # assigns stock.id
                        new_stocks_info.append((stock.id, stock.symbol))
                    elif not stock.is_active:
                        stock.is_active = True
                        stock.last_activated_at = today
                        session.add(stock)
                        logger.info("Reactivated dormant stock '%s' on %s", stock.symbol, today)

                    # ── Save DailySnapshot ───────────────────────────────
                    # Check for existing snapshot (upsert).
                    snap_stmt = select(DailySnapshot).where(
                        DailySnapshot.stock_id == stock.id,
                        DailySnapshot.screener_id == screener_row.id,
                        DailySnapshot.snapshot_date == today,
                    )
                    snap_result = await session.exec(snap_stmt)
                    existing_snap = snap_result.first()

                    if existing_snap:
                        existing_snap.ltp = scraped.ltp
                        existing_snap.volume = scraped.volume
                        existing_snap.change_pct = scraped.change_pct
                        existing_snap.raw_data = scraped.raw
                        session.add(existing_snap)
                    else:
                        session.add(
                            DailySnapshot(
                                stock_id=stock.id,
                                screener_id=screener_row.id,
                                ltp=scraped.ltp,
                                volume=scraped.volume,
                                change_pct=scraped.change_pct,
                                snapshot_date=today,
                                raw_data=scraped.raw,
                            )
                        )

                    # Add to batch for tagging
                    stocks_info.append((stock, scraped.ltp, scraped.change_pct))

                if stocks_info:
                    try:
                        await tagger.generate_tags_batch(
                            stocks_info=stocks_info,
                            screener_name=screener_row.name,
                            screener_id=screener_row.id,
                            session=session,
                        )
                    except Exception:
                        logger.exception("Batch tagging failed for screener %s", screener_row.name)

                await session.commit()

                # Queue background history backfill for new stocks (2-year daily prices)
                if new_stocks_info:
                    asyncio.create_task(
                        backfill_stocks_in_background(
                            stocks_to_backfill=new_stocks_info,
                            screener_id=screener_row.id,
                        )
                    )

                logger.info(
                    "Screener '%s' complete: %d stocks processed",
                    screener_row.name,
                    len(scraped_stocks),
                )

            # Materialize end-of-day sector performance from the snapshots
            # just written. This is additive and does not alter stock data.
            await ReturnsCalculator().calculate_daily_tag_returns(session, date.today())

            # Soft-delete stocks that have not appeared in any screener for >= 21 days
            await soft_delete_inactive_stocks(session, threshold_days=21)

    finally:
        await scraper.close()


async def soft_delete_inactive_stocks(
    session: AsyncSession,
    threshold_days: int = 21,
    reference_date: date | None = None,
) -> int:
    """Soft-delete stocks that have not appeared in any screener for threshold_days.

    A stock is marked inactive (is_active = False) if its latest DailySnapshot
    is older than (reference_date - threshold_days).
    Historical DailySnapshot and WeeklyReturns records remain intact.

    Returns:
        Number of stocks newly marked inactive.
    """
    today = reference_date or date.today()
    cutoff_date = today - timedelta(days=threshold_days)

    # Subquery finding max snapshot_date per stock
    max_snap_subq = (
        select(
            DailySnapshot.stock_id,
            func.max(DailySnapshot.snapshot_date).label("latest_snap"),
        )
        .group_by(DailySnapshot.stock_id)
        .subquery()
    )

    # Find active stocks whose latest snapshot is older than cutoff_date
    # or active stocks that have no snapshots and whose first_seen is older than cutoff_date
    stmt = (
        select(Stock)
        .outerjoin(max_snap_subq, Stock.id == max_snap_subq.c.stock_id)
        .where(
            Stock.is_active == True,  # noqa: E712
            (max_snap_subq.c.latest_snap < cutoff_date)
            | (
                (max_snap_subq.c.latest_snap.is_(None))
                & (func.date(Stock.first_seen) < cutoff_date)
            ),
        )
    )
    result = await session.exec(stmt)
    inactive_stocks = list(result.all())

    if not inactive_stocks:
        return 0

    for stock in inactive_stocks:
        stock.is_active = False
        session.add(stock)
        logger.info(
            "Soft-deleting inactive stock '%s' (not seen in %d+ days)",
            stock.symbol,
            threshold_days,
        )

    await session.commit()
    logger.info("Soft-deleted %d inactive stocks", len(inactive_stocks))
    return len(inactive_stocks)



async def weekly_returns_calc() -> None:
    """Compute weekly returns for all stocks and tag cohorts.

    Called every Monday at 7:00 AM IST.
    """
    calculator = ReturnsCalculator()
    async with async_session_factory() as session:
        processed = await calculator.calculate_recent_completed_weeks(session, weeks=3)
        logger.info("Completed weekly returns refreshed: %d stock rows", processed)


async def backfill_derived_returns() -> None:
    """Build new derived data from existing persistent snapshots after deploy."""
    calculator = ReturnsCalculator()
    async with async_session_factory() as session:
        daily_count = await calculator.backfill_daily_tag_returns(session)
        weekly_count = await calculator.calculate_recent_completed_weeks(session, weeks=3)
        logger.info(
            "Derived-return backfill complete: %d daily tag rows, %d weekly stock rows",
            daily_count,
            weekly_count,
        )


async def cleanup_old_snapshots() -> None:
    """Delete daily_snapshots older than SNAPSHOT_RETENTION_DAYS.

    Called every Sunday at midnight IST.

    WHY delete old data?
    - Render free PostgreSQL has a 1GB limit.
    - At ~500 rows/day, 90 days ≈ 45K rows — well within limits.
    - Weekly returns are preserved independently in weekly_returns table.
    """
    settings = get_settings()
    cutoff = date.today() - timedelta(days=settings.SNAPSHOT_RETENTION_DAYS)

    async with async_session_factory() as session:
        stmt = select(DailySnapshot).where(DailySnapshot.snapshot_date < cutoff)
        result = await session.exec(stmt)
        old_snapshots = list(result.all())

        for snap in old_snapshots:
            await session.delete(snap)

        await session.commit()
        logger.info("Cleaned up %d snapshots older than %s", len(old_snapshots), cutoff)


async def sync_market_holidays_job() -> None:
    """Sync official market holidays from Upstox API.

    Called biannually (January 1st and July 1st at midnight IST).
    """
    async with async_session_factory() as session:
        await sync_market_holidays_from_upstox(session)


def register_jobs() -> None:
    """Register all scheduled jobs on the module-level scheduler.

    Called once during app startup (lifespan).
    """
    # Daily screener fetch: Mon-Fri, 6:30 PM IST
    scheduler.add_job(
        daily_screener_fetch,
        CronTrigger(hour=18, minute=30, day_of_week="mon-fri", timezone="Asia/Kolkata"),
        id="daily_screener_fetch",
        name="Daily Screener Fetch",
        replace_existing=True,
    )

    # Weekly returns: Monday, 7:00 AM IST
    scheduler.add_job(
        weekly_returns_calc,
        CronTrigger(hour=7, minute=0, day_of_week="mon", timezone="Asia/Kolkata"),
        id="weekly_returns_calc",
        name="Weekly Returns Calculator",
        replace_existing=True,
    )

    # Cleanup: Sunday, midnight IST
    scheduler.add_job(
        cleanup_old_snapshots,
        CronTrigger(hour=0, minute=0, day_of_week="sun", timezone="Asia/Kolkata"),
        id="cleanup_old_snapshots",
        name="Cleanup Old Snapshots",
        replace_existing=True,
    )

    # Market holidays sync: Jan 1 & Jul 1 at midnight IST
    scheduler.add_job(
        sync_market_holidays_job,
        CronTrigger(month="1,7", day=1, hour=0, minute=0, timezone="Asia/Kolkata"),
        id="sync_market_holidays",
        name="Sync Market Holidays Calendar",
        replace_existing=True,
    )

    logger.info("Scheduled jobs registered: daily_fetch, weekly_returns, cleanup, holidays_sync")
