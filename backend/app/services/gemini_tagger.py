"""Gemini-powered sector/industry tag generator with Redis caching.

PATTERN: Cache-Aside (Lazy Loading)
────────────────────────────────────
1. Check Redis first   → HIT   → return immediately (cheapest)
2. Check DB second     → found → cache in Redis, return (medium cost)
3. Call Gemini last     → save  → DB + Redis, return (most expensive)

WHY this 3-tier approach?
- Gemini API calls cost rate-limit tokens (10 RPM, 1400 RPD on free tier).
- Most stocks don't change industry between runs.  "Reliance Industries"
  is always "oil & gas, petrochemicals, telecom" — no need to ask Gemini daily.
- Redis check: ~0.1ms.  DB check: ~2ms.  Gemini call: ~500ms.
  The caching avoids the expensive path 95%+ of the time.

WHY re-tag if LTP changes > 5%?
- A >5% LTP move *might* indicate a business pivot, sector re-classification,
  or merger.  In practice, this rarely triggers for stable large-caps, but
  catches edge cases like a company spinning off a division.
- The threshold is configurable via TAG_CHANGE_THRESHOLD in settings.

TAG PHILOSOPHY:
- Tags describe the BUSINESS DOMAIN: "auto ancillaries", "waste management"
- NOT market behaviour: no "momentum play", "breakout candidate"
- Exactly 3 tags per stock per screener — consistent, predictable.
"""

import json
import logging
from datetime import date

from google import genai
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import redis.asyncio as aioredis

from app.config import get_settings
from app.models.stock import DailySnapshot, Stock
from app.models.tag import StockTag, Tag
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


# ── Prompt template ──────────────────────────────────────────────────────
TAGGING_PROMPT = """You are a stock market sector classifier for the Indian equity market.
Given a stock's name, symbol, and available data, generate exactly 3 tags that describe
the BUSINESS DOMAIN and INDUSTRY of this company.

Tags should be specific industry sub-sectors like:
- "auto ancillaries", "EV components", "two-wheelers"
- "waste management", "water treatment", "renewable energy"
- "private banking", "insurance", "NBFCs"
- "IT services", "SaaS", "digital payments"
- "specialty chemicals", "agrochemicals", "pharmaceuticals"
- "cement", "steel", "infrastructure"

Do NOT generate tags about stock behavior (no "momentum", "breakout", "value pick").
Return ONLY a JSON array of exactly 3 lowercase strings.  No markdown, no explanation.

Stock: {name} ({symbol})
Sector: {sector}
LTP: ₹{ltp} | Change: {change_pct}%
Screener: {screener_name}"""


class GeminiTagger:
    """Generates sector/industry tags for stocks using Google Gemini.

    Manages the full lifecycle:
    1. Cache check (Redis → DB)
    2. Change detection (skip if stock hasn't moved significantly)
    3. Gemini API call with rate limiting
    4. Tag normalisation, DB upsert, and Redis caching

    Usage:
        tagger = GeminiTagger(rate_limiter, redis_client)
        tags = await tagger.generate_tags(stock, screener_name, screener_id, session)
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
        """Generate (or retrieve cached) sector tags for a stock.

        Returns:
            List of 3 lowercase tag strings.
        """
        cache_key = f"stock:tags:{stock.symbol}:{screener_id}"

        # ── Tier 1: Redis cache ──────────────────────────────────────────
        cached = await self._redis.get(cache_key)
        if cached:
            logger.debug("Cache HIT for %s (Redis)", stock.symbol)
            return json.loads(cached)

        # ── Tier 2: DB lookup + change detection ─────────────────────────
        existing_tags = await self._get_existing_tags(stock.id, session)

        if existing_tags:
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
                    await self._cache_tags(cache_key, existing_tags)
                    return existing_tags

        # ── Tier 3: Call Gemini ───────────────────────────────────────────
        logger.info("Calling Gemini for %s (new stock or LTP changed)", stock.symbol)
        new_tags = await self._call_gemini(
            stock=stock,
            ltp=current_ltp,
            change_pct=change_pct,
            screener_name=screener_name,
        )

        # ── Save to DB + Redis ───────────────────────────────────────────
        await self._upsert_tags(stock.id, screener_id, new_tags, session)
        await self._cache_tags(cache_key, new_tags)

        return new_tags

    # ── Private: Gemini API ──────────────────────────────────────────────

    async def _call_gemini(
        self,
        stock: Stock,
        ltp: float,
        change_pct: float | None,
        screener_name: str,
    ) -> list[str]:
        """Call Gemini API with rate limiting and response parsing.

        Retries up to 3 times with exponential backoff on transient errors.
        """
        prompt = TAGGING_PROMPT.format(
            name=stock.name,
            symbol=stock.symbol,
            sector=stock.sector or "Unknown",
            ltp=ltp,
            change_pct=change_pct or 0.0,
            screener_name=screener_name,
        )

        # Wait for rate limit token before calling.
        await self._rate_limiter.acquire()

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            raw_text = response.text.strip()
            tags = self._parse_tags(raw_text)
            logger.info("Gemini tags for %s: %s", stock.symbol, tags)
            return tags

        except Exception:
            logger.exception("Gemini API call failed for %s", stock.symbol)
            # Return a generic fallback so the pipeline doesn't break.
            return [stock.sector.lower() if stock.sector else "uncategorised"]

    @staticmethod
    def _parse_tags(raw_text: str) -> list[str]:
        """Parse Gemini's response into exactly 3 normalised tag strings.

        Gemini should return a JSON array, but sometimes wraps it in
        markdown code fences.  This handles both cases.
        """
        # Strip markdown code fences if present: ```json ... ```
        cleaned = raw_text.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        try:
            tags = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini response as JSON: %s", raw_text)
            # Last resort: split by comma/newline.
            tags = [t.strip().strip('"').strip("'") for t in raw_text.split(",")]

        # Normalise: lowercase, strip, take exactly 3.
        tags = [str(t).strip().lower() for t in tags if str(t).strip()]
        return tags[:3]

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

    async def _cache_tags(self, key: str, tags: list[str]) -> None:
        """Store tags in Redis with TTL."""
        await self._redis.setex(key, self._cache_ttl, json.dumps(tags))
