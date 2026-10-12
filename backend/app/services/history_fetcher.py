"""Historical price fetcher using Yahoo Finance.

Automatically backfills 2 years of daily price snapshots for newly added stocks,
ensuring multi-period returns (1w, 1m, 3m, 6m, 1y, 2y) and 52W high drawdown
are immediately available across the dashboard and stocks views.
"""

from datetime import date, datetime, timezone
import logging
from typing import Any

import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import async_session_factory
from app.models.stock import DailySnapshot

logger = logging.getLogger(__name__)


class HistoryFetcher:
    """Fetches historical daily close prices for Indian stocks from Yahoo Finance."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    async def fetch_history(
        self, symbol: str, range_str: str = "2y"
    ) -> list[dict[str, Any]]:
        """Fetch daily closing prices for an equity symbol.

        Tries NSE ({symbol}.NS) first, then BSE ({symbol}.BO) as fallback.
        Returns a list of dicts:
            [{"date": date, "ltp": float, "volume": int | None, "change_pct": float | None}, ...]
        sorted chronologically.
        """
        clean_symbol = symbol.strip().upper()
        # Candidates to try on Yahoo Finance
        candidates = [f"{clean_symbol}.NS", f"{clean_symbol}.BO", clean_symbol]

        async with httpx.AsyncClient(headers=self.HEADERS, timeout=self._timeout) as client:
            for ticker in candidates:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_str}&interval=1d"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    chart = data.get("chart", {})
                    result = chart.get("result")
                    if not result or not isinstance(result, list):
                        continue

                    series = result[0]
                    timestamps = series.get("timestamp", [])
                    indicators = series.get("indicators", {}).get("quote", [{}])[0]
                    closes = indicators.get("close", [])
                    volumes = indicators.get("volume", [])

                    if not timestamps or not closes:
                        continue

                    points: list[dict[str, Any]] = []
                    prev_close: float | None = None

                    for ts, close, vol in zip(timestamps, closes, volumes):
                        if close is None:
                            continue

                        pt_date = datetime.fromtimestamp(ts, tz=timezone.utc).date()
                        close_rounded = round(float(close), 2)

                        change_pct: float | None = None
                        if prev_close and prev_close > 0:
                            change_pct = round(
                                ((close_rounded - prev_close) / prev_close) * 100, 2
                            )
                        prev_close = close_rounded

                        points.append(
                            {
                                "date": pt_date,
                                "ltp": close_rounded,
                                "volume": int(vol) if vol is not None else None,
                                "change_pct": change_pct,
                            }
                        )

                    if points:
                        logger.info(
                            "Fetched %d historical price points for %s via %s",
                            len(points),
                            clean_symbol,
                            ticker,
                        )
                        return points

                except Exception as e:
                    logger.debug("Attempt to fetch history for %s via %s failed: %s", clean_symbol, ticker, e)

        logger.warning("Could not fetch historical data for symbol: %s from Yahoo Finance", clean_symbol)
        return []

    async def backfill_stock(
        self,
        stock_id: int,
        symbol: str,
        screener_id: int,
        session: AsyncSession,
        range_str: str = "2y",
    ) -> int:
        """Fetch history and insert missing DailySnapshot records for a stock."""
        points = await self.fetch_history(symbol, range_str=range_str)
        if not points:
            return 0

        # Query existing snapshot dates to avoid duplicate key errors
        existing_stmt = select(DailySnapshot.snapshot_date).where(
            DailySnapshot.stock_id == stock_id
        )
        existing_res = await session.exec(existing_stmt)
        existing_dates = set(existing_res.all())

        new_snapshots: list[DailySnapshot] = []
        for pt in points:
            if pt["date"] in existing_dates:
                continue

            existing_dates.add(pt["date"])
            new_snapshots.append(
                DailySnapshot(
                    stock_id=stock_id,
                    screener_id=screener_id,
                    ltp=pt["ltp"],
                    volume=pt["volume"],
                    change_pct=pt["change_pct"],
                    snapshot_date=pt["date"],
                    raw_data={"source": "yahoo_finance_backfill"},
                )
            )

        if new_snapshots:
            session.add_all(new_snapshots)
            await session.commit()
            logger.info(
                "Backfilled %d historical snapshots for %s (stock_id=%d)",
                len(new_snapshots),
                symbol,
                stock_id,
            )

        return len(new_snapshots)


async def backfill_stocks_in_background(
    stocks_to_backfill: list[tuple[int, str]], screener_id: int
) -> None:
    """Background worker function to backfill 2-year history for newly discovered stocks.

    Args:
        stocks_to_backfill: List of (stock_id, symbol)
        screener_id: Screener to associate provenance with
    """
    if not stocks_to_backfill:
        return

    logger.info("Starting background history backfill for %d new stocks", len(stocks_to_backfill))
    fetcher = HistoryFetcher()

    async with async_session_factory() as session:
        for stock_id, symbol in stocks_to_backfill:
            try:
                await fetcher.backfill_stock(
                    stock_id=stock_id,
                    symbol=symbol,
                    screener_id=screener_id,
                    session=session,
                )
            except Exception:
                logger.exception("Background history backfill failed for %s", symbol)

    logger.info("Completed background history backfill for %d new stocks", len(stocks_to_backfill))
