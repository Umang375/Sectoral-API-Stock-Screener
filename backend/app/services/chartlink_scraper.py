"""Chartlink screener scraper — data extraction from chartink.com.

PATTERN: Adapter
─────────────────
Wraps Chartlink's undocumented internal API behind a clean interface.
The rest of our codebase calls `scraper.run_screener(scan_clause)` and
gets back a list of typed dicts — it never knows about CSRF tokens,
POST endpoints, or HTML parsing.

HOW CHARTLINK WORKS INTERNALLY:
1. Visit chartink.com — the HTML contains a <meta name="csrf-token"> tag.
2. POST to /screener/process with:
   - Header: X-CSRF-TOKEN = <that token>
   - Body:   scan_clause = <the screener formula>
3. Response: JSON with a "data" array of stock rows.

WHY httpx.AsyncClient with a session?
- Chartlink uses cookies + CSRF tokens.  An httpx session (client)
  automatically persists cookies across requests, just like a browser.
- Async so we don't block the event loop during network I/O.

WHY a 2-second delay?
- Polite scraping.  Hitting their server faster risks IP bans.
  The delay is configurable via CHARTLINK_DELAY_SECONDS in settings.

FALLBACK: CSV Upload
- If POST simulation breaks (CAPTCHA, HTML changes), the `parse_csv()`
  method provides the same output shape from a manually exported CSV.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from io import StringIO

import httpx
import pandas as pd

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ScrapedStock:
    """Cleaned output from a Chartlink screener result.

    This is our INTERNAL representation — decoupled from Chartlink's
    raw JSON field names so we survive if they rename columns.
    """

    symbol: str
    name: str
    ltp: float
    volume: int | None = None
    change_pct: float | None = None
    raw: dict | None = None  # full original row for JSONB storage


class ChartlinkScraper:
    """Fetches stock data from Chartlink screeners.

    Usage:
        scraper = ChartlinkScraper()
        stocks = await scraper.run_screener("( {cash} ( latest close > 200 ) )")
        for stock in stocks:
            print(stock.symbol, stock.ltp)
        await scraper.close()
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.CHARTLINK_BASE_URL
        self._process_url = f"{self._base_url}/screener/process"
        self._delay = settings.CHARTLINK_DELAY_SECONDS

        # httpx client persists cookies across requests (like a browser session).
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=30.0,
            follow_redirects=True,
        )

    async def _fetch_csrf_token(self) -> str:
        """GET the Chartlink homepage and extract the CSRF token.

        Chartlink embeds a CSRF token in the HTML:
            <meta name="csrf-token" content="abc123...">
        We need this token in every POST request.

        WHY not hardcode a token?
        - CSRF tokens are session-bound and rotate. A stale token = 403 error.
        """
        logger.debug("Fetching CSRF token from %s", self._base_url)
        # Override Accept for this GET — we need HTML, not JSON.
        response = await self._client.get(
            f"{self._base_url}/screener",
            headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
        )
        response.raise_for_status()

        # Extract: <meta name="csrf-token" content="..."> or content="..."/>
        match = re.search(
            r'<meta\s+name="csrf-token"\s+content="([^"]+)"\s*/?>',
            response.text,
        )
        if not match:
            raise RuntimeError(
                "Could not extract CSRF token from Chartlink. "
                "The page structure may have changed."
            )

        token = match.group(1)
        logger.debug("CSRF token obtained (first 10 chars): %s...", token[:10])
        return token

    async def run_screener(self, scan_clause: str) -> list[ScrapedStock]:
        """Run a Chartlink screener and return parsed stock data.

        Args:
            scan_clause: The Chartlink scan formula, e.g.
                "( {cash} ( latest close > latest sma( close, 200 ) ) )"

        Returns:
            List of ScrapedStock objects.

        Raises:
            httpx.HTTPStatusError: If Chartlink returns a non-2xx response.
            RuntimeError: If CSRF token extraction fails.
        """
        token = await self._fetch_csrf_token()

        # Polite delay between the GET (CSRF) and POST (screener).
        await asyncio.sleep(self._delay)

        logger.info("Running screener: %s...", scan_clause[:80])
        response = await self._client.post(
            self._process_url,
            data={"scan_clause": scan_clause},
            headers={"X-CSRF-TOKEN": token},
        )
        response.raise_for_status()

        payload = response.json()
        raw_rows = payload.get("data", [])
        logger.info("Screener returned %d stocks", len(raw_rows))

        return [self._parse_row(row) for row in raw_rows]

    def _parse_row(self, row: dict) -> ScrapedStock:
        """Convert a raw Chartlink JSON row into our internal format.

        Chartlink's JSON keys vary slightly between screeners, but common
        fields are: nsecode, name, close, volume, per_chg.  We map them
        to our stable ScrapedStock structure.
        """
        return ScrapedStock(
            symbol=str(row.get("nsecode", row.get("symbol", ""))).upper().strip(),
            name=str(row.get("name", "")).strip(),
            ltp=float(row.get("close", row.get("ltp", 0))),
            volume=int(row["volume"]) if row.get("volume") else None,
            change_pct=float(row["per_chg"]) if row.get("per_chg") else None,
            raw=row,
        )

    @staticmethod
    def parse_csv(csv_content: str) -> list[ScrapedStock]:
        """Parse a Chartlink CSV export into ScrapedStock objects.

        This is the FALLBACK path — used when POST simulation breaks.
        Users download CSV from Chartlink manually and upload it via the API.

        Expected CSV columns (case-insensitive):
            Sr, Symbol (or Stock Name), Name, LTP (or Close), Volume, Change%
        """
        df = pd.read_csv(StringIO(csv_content))

        # Normalise column names: lowercase, strip whitespace.
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Map various column naming conventions Chartlink uses.
        symbol_col = _find_column(df, ["symbol", "nsecode", "stock_name"])
        name_col = _find_column(df, ["name", "company_name", "stock"])
        ltp_col = _find_column(df, ["ltp", "close", "last_price"])
        volume_col = _find_column(df, ["volume", "vol"])
        change_col = _find_column(df, ["change%", "per_chg", "change_pct", "%_change"])

        results: list[ScrapedStock] = []
        for _, row in df.iterrows():
            results.append(
                ScrapedStock(
                    symbol=str(row[symbol_col]).upper().strip() if symbol_col else "",
                    name=str(row[name_col]).strip() if name_col else "",
                    ltp=float(row[ltp_col]) if ltp_col and pd.notna(row[ltp_col]) else 0.0,
                    volume=(
                        int(row[volume_col])
                        if volume_col and pd.notna(row.get(volume_col))
                        else None
                    ),
                    change_pct=(
                        float(row[change_col])
                        if change_col and pd.notna(row.get(change_col))
                        else None
                    ),
                    raw=row.to_dict(),
                )
            )

        logger.info("Parsed %d stocks from CSV", len(results))
        return results

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find the first matching column name from a list of candidates.

    Returns None if no candidate matches.  This makes CSV parsing robust
    against different Chartlink export formats.
    """
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None
