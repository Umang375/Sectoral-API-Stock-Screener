"""Gemini-powered sector/industry tag generator and sector classifier with Redis caching.

PATTERN: Cache-Aside (Lazy Loading)
────────────────────────────────────
1. Check Redis first   → HIT   → return immediately (cheapest)
2. Check DB second     → found → cache in Redis, return (medium cost)
3. Call Gemini last     → save  → DB + Redis, return (most expensive)

WHY this 3-tier approach?
- Gemini API calls cost rate-limit tokens (10 RPM, 1400 RPD on free tier).
- Most stocks don't change industry between runs. "Reliance Industries"
  is always "oil & gas, petrochemicals, telecom" — no need to ask Gemini daily.
- Redis check: ~0.1ms.  DB check: ~2ms.  Gemini call: ~500ms.
  The caching avoids the expensive path 95%+ of the time.

WHY re-tag if LTP changes > 5%?
- A >5% LTP move *might* indicate a business pivot, sector re-classification,
  or merger. In practice, this rarely triggers for stable large-caps, but
  catches edge cases like a company spinning off a division.
- The threshold is configurable via TAG_CHANGE_THRESHOLD in settings.

TAG & SECTOR PHILOSOPHY:
- Sector: Exactly 1 primary category selected strictly from the predefined
  list of 80+ standard equity sectors (e.g. "Auto Ancillary", "IT Large Cap").
- Tags: Exactly 3 lowercase tags describing the granular BUSINESS DOMAIN:
  "auto ancillaries", "EV components", "batteries".
- NOT market behaviour: no "momentum play", "breakout candidate".
"""

import json
import logging
from datetime import date
from typing import Any

from google import genai
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import redis.asyncio as aioredis

from app.config import get_settings
from app.constants.sectors import (
    FALLBACK_SECTOR,
    format_sectors_for_prompt,
    normalize_sector,
)
from app.models.stock import DailySnapshot, Stock
from app.models.tag import StockTag, Tag
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


# ── Prompt template ──────────────────────────────────────────────────────
UNIFIED_TAGGING_PROMPT = """You are a stock market sector and industry classifier for the Indian equity market.
Given a list of stocks with their available data:
1. Select EXACTLY ONE primary sector for each stock from the PREDEFINED SECTORS list below.
2. Generate EXACTLY 3 tags that describe the specific BUSINESS DOMAIN and sub-industry of the company.

Tags should be specific industry sub-sectors like:
- "auto ancillaries", "EV components", "two-wheelers"
- "waste management", "water treatment", "renewable energy"
- "private banking", "insurance", "NBFCs"
- "IT services", "SaaS", "digital payments"
- "specialty chemicals", "agrochemicals", "pharmaceuticals"
- "cement", "steel", "infrastructure"

Do NOT generate tags about stock behavior (no "momentum", "breakout", "value pick").

PREDEFINED SECTORS (Choose exactly one for each stock):
{predefined_sectors}

Return ONLY a valid JSON object mapping each stock symbol to an object with "sector" and "tags". No markdown code fences, no explanation.

Example Output format:
{{
  "RELIANCE": {{
    "sector": "Oil Refiners",
    "tags": ["oil & gas", "petrochemicals", "telecom"]
  }},
  "TCS": {{
    "sector": "IT Large Cap",
    "tags": ["it services", "cloud computing", "saas"]
  }}
}}

Screener: {screener_name}

Stocks to tag:
{stocks_data}"""


class GeminiTagger:
    """Generates sector/industry tags and classifies stocks using Google Gemini.

    Manages the full lifecycle:
    1. Cache check (Redis → DB)
    2. Change detection (skip if stock hasn't moved significantly and already has sector)
    3. Gemini API call with rate limiting
    4. Tag normalisation, sector validation, DB upsert, and Redis caching
    """

    def __init__(self, rate_limiter: RateLimiter, redis: aioredis.Redis) -> None:
        settings = get_settings()
        self._model_name = settings.GEMINI_MODEL
        self._cache_ttl = settings.TAG_CACHE_TTL_SECONDS
        self._change_threshold = settings.TAG_CHANGE_THRESHOLD
        self._rate_limiter = rate_limiter
        self._redis = redis

        # Initialise the Gemini client.
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # ── Public API ───────────────────────────────────────────────────────

    async def generate_tags(
        self,
        stock: Stock,
        current_ltp: float,
        change_pct: float | None,
        screener_name: str,
        screener_id: int,
        session: AsyncSession,
    ) -> list[str]:
        """Generate (or retrieve cached) sector tags and classification for a stock.

        Returns:
            List of 3 lowercase tag strings.
        """
        cache_key = f"stock:tags:{stock.symbol}:{screener_id}"

        # ── Tier 1: Redis cache ──────────────────────────────────────────
        cached = await self._redis.get(cache_key)
        if cached:
            logger.debug("Cache HIT for %s (Redis)", stock.symbol)
            cached_data = json.loads(cached)
            if isinstance(cached_data, dict):
                return cached_data.get("tags", [])
            return cached_data

        # ── Tier 2: DB lookup + change detection ─────────────────────────
        existing_tags = await self._get_existing_tags(stock.id, session)

        if existing_tags and stock.sector:
            # Check if stock has changed enough to warrant re-tagging.
            last_ltp = await self._get_last_ltp(stock.id, session)
            if last_ltp and last_ltp > 0:
                ltp_change = abs(current_ltp - last_ltp) / last_ltp
                if ltp_change < self._change_threshold:
                    # Stock is stable — use existing tags, cache them.
                    logger.debug(
                        "Cache HIT for %s (DB, LTP change %.1f%% < threshold)",
                        stock.symbol,
                        ltp_change * 100,
                    )
                    await self._cache_tags(
                        cache_key,
                        {"tags": existing_tags, "sector": stock.sector},
                    )
                    return existing_tags

        # ── Tier 3: Call Gemini via unified batch pipeline ───────────────
        logger.info(
            "Calling Gemini for %s via unified pipeline (new stock, unclassified sector, or LTP changed)",
            stock.symbol,
        )
        await self.generate_tags_batch(
            stocks_info=[(stock, current_ltp, change_pct)],
            screener_name=screener_name,
            screener_id=screener_id,
            session=session,
        )

        return await self._get_existing_tags(stock.id, session)

    async def generate_tags_batch(
        self,
        stocks_info: list[tuple[Stock, float, float | None]],
        screener_name: str,
        screener_id: int,
        session: AsyncSession,
    ) -> None:
        """Batch process tags and sector classification for multiple stocks.

        Args:
            stocks_info: List of (Stock, current_ltp, change_pct)
        """
        needs_gemini: list[tuple[Stock, float, float | None]] = []

        for stock, current_ltp, change_pct in stocks_info:
            cache_key = f"stock:tags:{stock.symbol}:{screener_id}"

            # ── Tier 1: Redis cache ──────────────────────────────────────────
            cached = await self._redis.get(cache_key)
            if cached:
                logger.debug("Cache HIT for %s (Redis)", stock.symbol)
                continue

            # ── Tier 2: DB lookup + change detection ─────────────────────────
            existing_tags = await self._get_existing_tags(stock.id, session)

            if existing_tags and stock.sector:
                last_ltp = await self._get_last_ltp(stock.id, session)
                if last_ltp and last_ltp > 0:
                    ltp_change = abs(current_ltp - last_ltp) / last_ltp
                    if ltp_change < self._change_threshold:
                        logger.debug(
                            "Cache HIT for %s (DB, LTP change %.1f%% < threshold)",
                            stock.symbol,
                            ltp_change * 100,
                        )
                        await self._cache_tags(
                            cache_key,
                            {"tags": existing_tags, "sector": stock.sector},
                        )
                        continue

            # Needs Gemini call
            needs_gemini.append((stock, current_ltp, change_pct))

        if not needs_gemini:
            return

        # ── Tier 3: Call Gemini in batches ──────────────────────────────────
        batch_size = get_settings().TAG_BATCH_SIZE
        for i in range(0, len(needs_gemini), batch_size):
            batch = needs_gemini[i:i + batch_size]
            logger.info("Calling Gemini for batch of %d stocks", len(batch))

            batch_results = await self._call_gemini_batch(
                stocks_info=batch,
                screener_name=screener_name,
            )

            # ── Save to DB + Redis ───────────────────────────────────────────
            for stock, _, _ in batch:
                if stock.symbol in batch_results:
                    res = batch_results[stock.symbol]
                    tags = res["tags"]
                    sector = res["sector"]

                    stock.sector = sector
                    session.add(stock)

                    cache_key = f"stock:tags:{stock.symbol}:{screener_id}"
                    await self._upsert_tags(stock.id, screener_id, tags, session)
                    await self._cache_tags(
                        cache_key,
                        {"tags": tags, "sector": sector},
                    )

            await session.commit()

    # ── Private: Gemini API ──────────────────────────────────────────────

    async def _call_gemini_batch(
        self,
        stocks_info: list[tuple[Stock, float, float | None]],
        screener_name: str,
    ) -> dict[str, dict[str, Any]]:
        """Call Gemini API for a batch of 1 to N stocks and return mappings."""
        stocks_data = []
        for stock, ltp, change_pct in stocks_info:
            stocks_data.append(
                f"- Symbol: {stock.symbol}, Name: {stock.name}, Sector: {stock.sector or 'Unknown'}, "
                f"LTP: ₹{ltp}, Change: {change_pct or 0.0}%"
            )

        prompt = UNIFIED_TAGGING_PROMPT.format(
            screener_name=screener_name,
            stocks_data="\n".join(stocks_data),
            predefined_sectors=format_sectors_for_prompt(),
        )

        try:
            await self._rate_limiter.acquire()

            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            raw_text = response.text.strip()
            return self._parse_tags_batch(raw_text, [s[0] for s in stocks_info])
        except Exception:
            logger.exception("Gemini batch API call failed")
            result: dict[str, dict[str, Any]] = {}
            for stock, _, _ in stocks_info:
                sec = normalize_sector(stock.sector)
                result[stock.symbol] = {
                    "sector": sec,
                    "tags": [sec.lower()],
                }
            return result

    @staticmethod
    def _parse_tags_batch(
        raw_text: str, stocks: list[Stock]
    ) -> dict[str, dict[str, Any]]:
        """Parse Gemini's batch response into a dict of {sector, tags} per stock."""
        cleaned = raw_text.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        result: dict[str, dict[str, Any]] = {}
        try:
            parsed_json = json.loads(cleaned)
            for stock in stocks:
                if stock.symbol in parsed_json:
                    item = parsed_json[stock.symbol]
                    if isinstance(item, dict):
                        raw_sector = item.get("sector", stock.sector)
                        raw_tags = item.get("tags", [])
                        tags = (
                            [str(t).strip().lower() for t in raw_tags if str(t).strip()]
                            if isinstance(raw_tags, list)
                            else []
                        )
                    elif isinstance(item, list):
                        raw_sector = stock.sector
                        tags = [str(t).strip().lower() for t in item if str(t).strip()]
                    else:
                        raw_sector = stock.sector
                        tags = []

                    sector = normalize_sector(raw_sector)
                    if not tags:
                        tags = [sector.lower()]

                    result[stock.symbol] = {
                        "sector": sector,
                        "tags": tags[:3],
                    }
                else:
                    sec = normalize_sector(stock.sector)
                    result[stock.symbol] = {
                        "sector": sec,
                        "tags": [sec.lower()],
                    }
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini batch response as JSON: %s", raw_text)
            for stock in stocks:
                sec = normalize_sector(stock.sector)
                result[stock.symbol] = {
                    "sector": sec,
                    "tags": [sec.lower()],
                }
            return result

    # ── Private: DB operations ───────────────────────────────────────────

    @staticmethod
    async def _get_existing_tags(stock_id: int, session: AsyncSession) -> list[str]:
        """Fetch current tags for a stock from the database."""
        stmt = (
            select(Tag.label)
            .join(StockTag, StockTag.tag_id == Tag.id)
            .where(StockTag.stock_id == stock_id)
        )
        result = await session.exec(stmt)
        return list(result.all())

    @staticmethod
    async def _get_last_ltp(stock_id: int, session: AsyncSession) -> float | None:
        """Get the most recent LTP for a stock from daily_snapshots."""
        stmt = (
            select(DailySnapshot.ltp)
            .where(DailySnapshot.stock_id == stock_id)
            .order_by(DailySnapshot.snapshot_date.desc())
            .limit(1)
        )
        result = await session.exec(stmt)
        return result.first()

    @staticmethod
    async def _upsert_tags(
        stock_id: int,
        screener_id: int,
        tag_labels: list[str],
        session: AsyncSession,
    ) -> None:
        """Insert or update tags for a stock.

        1. Ensure each tag label exists in the `tags` table (get-or-create).
        2. Link the stock to each tag via `stock_tags` (upsert).
        """
        today = date.today()

        for label in tag_labels:
            # Get or create the Tag record.
            stmt = select(Tag).where(Tag.label == label)
            result = await session.exec(stmt)
            tag = result.first()

            if not tag:
                tag = Tag(label=label)
                session.add(tag)
                await session.flush()  # assigns tag.id

            # Check if stock-tag link already exists.
            link_stmt = select(StockTag).where(
                StockTag.stock_id == stock_id,
                StockTag.tag_id == tag.id,
            )
            link_result = await session.exec(link_stmt)
            existing_link = link_result.first()

            if existing_link:
                # Update the date and screener (tag label unchanged).
                existing_link.tagged_on = today
                existing_link.screener_id = screener_id
                session.add(existing_link)
            else:
                session.add(
                    StockTag(
                        stock_id=stock_id,
                        tag_id=tag.id,
                        screener_id=screener_id,
                        tagged_on=today,
                        source="gemini",
                    )
                )

        await session.commit()

    # ── Private: Redis caching ───────────────────────────────────────────

    async def _cache_tags(self, key: str, payload: list[str] | dict[str, Any]) -> None:
        """Store tags and sector classification in Redis with TTL."""
        await self._redis.setex(key, self._cache_ttl, json.dumps(payload))
