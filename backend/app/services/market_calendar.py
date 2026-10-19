"""Indian Stock Market (NSE / BSE) Trading Calendar Service.

Manages official equity market trading holidays with dynamic synchronization
from the Upstox Open API, local database persistence, and microsecond-level
in-memory caching.
"""

from datetime import date, datetime, timedelta
import logging
from typing import Any

import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import async_session_factory
from app.models.calendar import MarketHoliday

logger = logging.getLogger(__name__)

UPSTOX_HOLIDAYS_URL = "https://api.upstox.com/v2/market/holidays"

# In-memory cached set of trading holidays for O(1) performance
_HOLIDAY_CACHE: set[date] = set()

# Built-in baseline seed (2024-2026) ensuring instant offline boot
BASELINE_HOLIDAYS_SEED: dict[date, str] = {
    # 2024
    date(2024, 1, 22): "Special Holiday",
    date(2024, 1, 26): "Republic Day",
    date(2024, 3, 8): "Mahashivratri",
    date(2024, 3, 25): "Holi",
    date(2024, 3, 29): "Good Friday",
    date(2024, 4, 11): "Id-Ul-Fitr",
    date(2024, 4, 17): "Ram Navami",
    date(2024, 5, 1): "Maharashtra Day",
    date(2024, 5, 20): "General Elections",
    date(2024, 6, 17): "Bakri Id",
    date(2024, 7, 17): "Moharram",
    date(2024, 8, 15): "Independence Day",
    date(2024, 10, 2): "Mahatma Gandhi Jayanti",
    date(2024, 11, 1): "Diwali Laxmi Pujan",
    date(2024, 11, 15): "Gurunanak Jayanti",
    date(2024, 12, 25): "Christmas",
    # 2025
    date(2025, 2, 26): "Mahashivratri",
    date(2025, 3, 14): "Holi",
    date(2025, 3, 31): "Id-Ul-Fitr",
    date(2025, 4, 10): "Mahavir Jayanti",
    date(2025, 4, 14): "Dr. Baba Saheb Ambedkar Jayanti",
    date(2025, 4, 18): "Good Friday",
    date(2025, 5, 1): "Maharashtra Day",
    date(2025, 8, 15): "Independence Day",
    date(2025, 8, 27): "Ganesh Chaturthi",
    date(2025, 10, 2): "Mahatma Gandhi Jayanti / Dussehra",
    date(2025, 10, 21): "Diwali Balipratipada",
    date(2025, 11, 5): "Prakash Gurpurb",
    date(2025, 12, 25): "Christmas",
    # 2026 (From official Upstox Holiday Master)
    date(2026, 1, 15): "Municipal Corporation Election",
    date(2026, 1, 26): "Republic Day",
    date(2026, 3, 3): "Holi",
    date(2026, 3, 26): "Ram Navami",
    date(2026, 3, 31): "Mahavir Jayanti",
    date(2026, 4, 3): "Good Friday",
    date(2026, 4, 14): "Dr. Baba Saheb Ambedkar Jayanti",
    date(2026, 5, 1): "Maharashtra Day",
    date(2026, 5, 28): "Bakri Id / Eid-ul-Adha",
    date(2026, 6, 26): "Muharram",
    date(2026, 9, 14): "Ganesh Chaturthi",
    date(2026, 10, 2): "Gandhi Jayanti",
    date(2026, 10, 20): "Dussehra",
    date(2026, 11, 10): "Diwali-Balipratipada",
    date(2026, 11, 24): "Guru Nanak Jayanti",
    date(2026, 12, 25): "Christmas",
}


def is_trading_day(d: date) -> bool:
    """Return True if the date is an active Monday-Friday market trading session.

    Returns False for Saturdays, Sundays, and official equity market trading holidays.
    """
    if d.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    return d not in _HOLIDAY_CACHE


def get_expected_trading_days(week_start: date, week_end: date) -> int:
    """Calculate the expected number of market trading days between week_start and week_end.

    Accounts for weekends and any intervening NSE/BSE holidays (e.g. returns 4 during
    a week with a public holiday like Good Friday or Holi).
    """
    count = 0
    curr = week_start
    while curr <= week_end:
        if is_trading_day(curr):
            count += 1
        curr += timedelta(days=1)
    return max(1, count)


async def seed_baseline_holidays(session: AsyncSession) -> int:
    """Seed baseline holidays into database if market_holidays table is empty."""
    stmt = select(MarketHoliday.id).limit(1)
    res = await session.exec(stmt)
    if res.first():
        return 0

    logger.info("Seeding %d baseline market holidays into database...", len(BASELINE_HOLIDAYS_SEED))
    for h_date, desc in BASELINE_HOLIDAYS_SEED.items():
        session.add(
            MarketHoliday(
                holiday_date=h_date,
                description=desc,
                holiday_type="TRADING_HOLIDAY",
                closed_exchanges="NSE,BSE",
                year=h_date.year,
            )
        )
    await session.commit()
    return len(BASELINE_HOLIDAYS_SEED)


async def load_market_calendar_cache(session: AsyncSession) -> int:
    """Load all trading holidays from database into in-memory set for O(1) checks."""
    global _HOLIDAY_CACHE

    await seed_baseline_holidays(session)

    stmt = select(MarketHoliday.holiday_date).where(MarketHoliday.holiday_type == "TRADING_HOLIDAY")
    res = await session.exec(stmt)
    dates = set(res.all())

    if dates:
        _HOLIDAY_CACHE = dates
    else:
        _HOLIDAY_CACHE = set(BASELINE_HOLIDAYS_SEED.keys())

    logger.debug("Market calendar cache loaded with %d trading holidays", len(_HOLIDAY_CACHE))
    return len(_HOLIDAY_CACHE)


async def sync_market_holidays_from_upstox(session: AsyncSession) -> dict[str, Any]:
    """Fetch official holiday calendar from Upstox API and upsert into database.

    Filter rules:
    - holiday_type must be "TRADING_HOLIDAY" (skips settlement-only & special sessions)
    - closed_exchanges must include "NSE" or "BSE"
    """
    logger.info("Syncing market holidays from Upstox API: %s", UPSTOX_HOLIDAYS_URL)
    new_count = 0
    updated_count = 0

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(UPSTOX_HOLIDAYS_URL)
            resp.raise_for_status()
            payload = resp.json()

        data = payload.get("data", [])
        for item in data:
            holiday_type = item.get("holiday_type")
            closed_exchanges = item.get("closed_exchanges", [])

            # Filter strictly for equity TRADING_HOLIDAY on NSE or BSE
            if holiday_type != "TRADING_HOLIDAY":
                continue

            has_equity_exchange = any(exc in closed_exchanges for exc in ("NSE", "BSE"))
            if not has_equity_exchange:
                continue

            date_str = item.get("date")
            if not date_str:
                continue

            h_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            desc = item.get("description", "Market Holiday")
            closed_str = ",".join(closed_exchanges)

            stmt = select(MarketHoliday).where(MarketHoliday.holiday_date == h_date)
            existing = (await session.exec(stmt)).first()

            if existing:
                if existing.description != desc or existing.closed_exchanges != closed_str:
                    existing.description = desc
                    existing.closed_exchanges = closed_str
                    session.add(existing)
                    updated_count += 1
            else:
                session.add(
                    MarketHoliday(
                        holiday_date=h_date,
                        description=desc,
                        holiday_type=holiday_type,
                        closed_exchanges=closed_str,
                        year=h_date.year,
                    )
                )
                new_count += 1

        await session.commit()
        await load_market_calendar_cache(session)
        logger.info(
            "Market holiday sync completed successfully: %d added, %d updated",
            new_count,
            updated_count,
        )
        return {"status": "ok", "added": new_count, "updated": updated_count}

    except Exception as e:
        logger.warning("Could not sync holidays from Upstox API: %s. Relying on cached DB/seed.", e)
        await load_market_calendar_cache(session)
        return {"status": "error", "error": str(e)}


async def init_market_calendar() -> None:
    """Initialize calendar during application startup."""
    async with async_session_factory() as session:
        await load_market_calendar_cache(session)
