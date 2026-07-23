"""Async Redis client with lazy initialisation.

WHY a module-level singleton?
- Redis connections are expensive to create; we reuse a single connection pool
  across the entire process.
- Lazy init means importing this module doesn't immediately connect — useful for
  tests and CLI tools that don't need Redis at import time.
"""

import redis.asyncio as aioredis

from app.config import get_settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis instance, creating it on first call.

    The connection pool is created lazily so we don't block module import
    and can respect settings that may be overridden in tests.
    """
    global _redis  # noqa: PLW0603
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Gracefully close the Redis connection pool.

    Called during application shutdown to release sockets cleanly.
    """
    global _redis  # noqa: PLW0603
    if _redis is not None:
        await _redis.aclose()
        _redis = None
