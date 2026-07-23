"""Token-bucket rate limiter for the Gemini API.

PATTERN: Token Bucket
─────────────────────
Imagine a bucket that holds `capacity` tokens.  Every `refill_interval`
seconds, the bucket is refilled to `capacity`.  Each API call takes one
token.  If the bucket is empty, callers wait (async sleep) until the
next refill.

WHY this approach?
- Gemini free tier is ~10-15 RPM and ~1500 RPD.  A naive `time.sleep(6)`
  between calls wastes time when the bucket isn't empty.
- Token bucket allows BURSTS (fire 10 requests instantly if you have 10
  tokens) then naturally throttles once the bucket drains.
- The daily limiter is a separate check on top — hard-stop at RPD.

WHY async?
- `await asyncio.sleep()` releases the event loop so other requests
  keep being served while this one waits for a token.  A sync sleep
  would freeze the entire server.

USAGE:
    limiter = RateLimiter(rpm=10, rpd=1400)
    await limiter.acquire()  # blocks until a token is available
    response = await call_gemini(...)
"""

import asyncio
import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Async token-bucket rate limiter with per-minute and per-day limits.

    Thread-safe within a single async event loop (no multi-process support —
    for that, use Redis-backed counters).
    """

    def __init__(self, rpm: int = 10, rpd: int = 1400) -> None:
        # ── Per-minute bucket ────────────────────────────────────────────
        self._rpm = rpm
        self._minute_tokens: float = float(rpm)
        self._last_refill: float = time.monotonic()

        # ── Per-day counter ──────────────────────────────────────────────
        self._rpd = rpd
        self._day_remaining: int = rpd
        self._day_start: float = time.monotonic()

        # ── Concurrency guard ────────────────────────────────────────────
        # Ensures only one coroutine modifies token counts at a time.
        self._lock = asyncio.Lock()

    def _refill_minute_tokens(self) -> None:
        """Add tokens proportional to elapsed time since last refill.

        If 6 seconds have passed and RPM=10, that's 1 token added
        (10 tokens / 60 seconds × 6 seconds = 1 token).
        """
        now = time.monotonic()
        elapsed = now - self._last_refill
        new_tokens = elapsed * (self._rpm / 60.0)
        self._minute_tokens = min(self._rpm, self._minute_tokens + new_tokens)
        self._last_refill = now

    def _maybe_reset_daily(self) -> None:
        """Reset the daily counter if 24 hours have passed."""
        now = time.monotonic()
        if now - self._day_start >= 86_400:  # 24 hours
            self._day_remaining = self._rpd
            self._day_start = now
            logger.info("Daily rate limit counter reset (%d RPD)", self._rpd)

    async def acquire(self) -> None:
        """Wait until a rate-limit token is available, then consume it.

        Raises RuntimeError if the daily limit is exhausted.
        """
        async with self._lock:
            self._maybe_reset_daily()

            if self._day_remaining <= 0:
                raise RuntimeError(
                    f"Gemini daily rate limit exhausted ({self._rpd} RPD). "
                    "Wait until tomorrow or upgrade to a paid tier."
                )

            self._refill_minute_tokens()

            # Wait if per-minute bucket is empty.
            while self._minute_tokens < 1.0:
                # Calculate wait time: how long until 1 token refills?
                wait_seconds = (1.0 - self._minute_tokens) / (self._rpm / 60.0)
                logger.debug("Rate limited — waiting %.1fs for next token", wait_seconds)
                await asyncio.sleep(wait_seconds)
                self._refill_minute_tokens()

            # Consume one token from both buckets.
            self._minute_tokens -= 1.0
            self._day_remaining -= 1

    @property
    def day_remaining(self) -> int:
        """How many daily requests are left."""
        return self._day_remaining

    @property
    def minute_tokens(self) -> float:
        """Current per-minute tokens (approximate — not refilled until acquire)."""
        return self._minute_tokens
