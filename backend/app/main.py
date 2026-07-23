"""FastAPI application entry-point.

Responsibilities:
1. Wire up the lifespan (startup / shutdown) for DB, Redis, and scheduler.
2. Configure CORS so the Next.js frontend can talk to us.
3. Mount all API routers under /api/*.
4. Expose a /api/health route for liveness probes.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.redis_client import close_redis, get_redis
from app.services.scheduler import register_jobs, scheduler
from app.routers import stocks, tags, screeners, dashboard, webhooks
from app.utils.logging_config import setup_logging

# Configure logging before anything else.
setup_logging(get_settings().ENVIRONMENT)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown resources.

    Using the modern lifespan pattern (replaces deprecated on_event).
    """
    settings = get_settings()

    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Starting Sectoral API [%s]", settings.ENVIRONMENT)
    await init_db()
    logger.info("Database tables ensured")
    await get_redis()
    logger.info("Redis connection established")

    # Start background scheduler (daily fetch, weekly returns, cleanup).
    register_jobs()
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))

    yield  # ← application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
    await close_redis()
    logger.info("Redis connection closed")
    logger.info("Sectoral API shut down cleanly")


settings = get_settings()

app = FastAPI(
    title="Sectoral API",
    description="Stock screener tag & returns tracker for Indian equities",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(stocks.router)
app.include_router(tags.router)
app.include_router(screeners.router)
app.include_router(dashboard.router)
app.include_router(webhooks.router)


# ── Health check ─────────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Liveness probe — returns 200 if the server is up."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}
