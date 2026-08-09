"""Screener API router — manage and run Chartlink screeners.

This router serves TWO purposes:
1. CRUD for screener configurations (add/list/update screener formulas).
2. Manual trigger endpoints (run a screener now, upload CSV).

WHY manual triggers?
- The scheduler auto-runs at 6:30 PM daily, but sometimes you need
  to test a new screener formula immediately without waiting for the cron.
- The CSV upload is the fallback when POST simulation breaks.

SECURITY NOTE:
- These are admin-only operations — in production, add auth middleware.
- For the MVP (you as the only writer), no auth is needed yet.
"""

from datetime import date
from io import StringIO
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.database import get_session, async_session_factory
from app.models.screener import Screener
from app.models.stock import DailySnapshot, Stock
from app.redis_client import get_redis
from app.services.chartlink_scraper import ChartlinkScraper, ScrapedStock
from app.services.gemini_tagger import GeminiTagger
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screeners", tags=["screeners"])


# ── Request schemas (co-located because they're only used here) ──────────
class ScreenerCreate(BaseModel):
    """Request body for creating a new screener."""
    name: str
    scan_clause: str


class ScreenerUpdate(BaseModel):
    """Request body for updating a screener."""
    name: str | None = None
    scan_clause: str | None = None
    is_active: bool | None = None


class ScreenerResponse(BaseModel):
    """Response schema for screener endpoints."""
    id: int
    name: str
    scan_clause: str
    is_active: bool


class RunResult(BaseModel):
    """Response from running a screener."""
    screener: str
    stocks_fetched: int
    stocks_tagged: int
    message: str


# ── Background Worker ────────────────────────────────────────────────────

async def _tag_stocks_in_background(
    scraped_stocks: list[ScrapedStock],
    screener_name: str,
    screener_id: int
) -> None:
    """Run Gemini tagging in the background after the API responds.
    
    This respects rate limits without blocking the frontend response.
    """
    settings = get_settings()
    redis = await get_redis()
    rate_limiter = RateLimiter(rpm=settings.GEMINI_RPM, rpd=settings.GEMINI_RPD)
    tagger = GeminiTagger(rate_limiter=rate_limiter, redis=redis)

    async with async_session_factory() as session:
        stocks_info = []
        for stock_data in scraped_stocks:
            if not stock_data.symbol:
                continue

            # Fetch the stock from DB (it was inserted by the main thread)
            stock_stmt = select(Stock).where(Stock.symbol == stock_data.symbol)
            stock_result = await session.exec(stock_stmt)
            stock = stock_result.first()
            if stock:
                stocks_info.append((stock, stock_data.ltp, stock_data.change_pct))

        if stocks_info:
            try:
                await tagger.generate_tags_batch(
                    stocks_info=stocks_info,
                    screener_name=screener_name,
                    screener_id=screener_id,
                    session=session,
                )
            except Exception:
                logger.exception("Background batch tagging failed for screener %s", screener_name)


# ── CRUD endpoints ───────────────────────────────────────────────────────

@router.get("", response_model=list[ScreenerResponse])
async def list_screeners(
    session: AsyncSession = Depends(get_session),
) -> list[ScreenerResponse]:
    """List all configured screeners."""
    stmt = select(Screener).order_by(Screener.id)
    result = await session.exec(stmt)
    screeners = list(result.all())

    return [
        ScreenerResponse(
            id=s.id, name=s.name, scan_clause=s.scan_clause, is_active=s.is_active
        )
        for s in screeners
    ]


@router.post("", response_model=ScreenerResponse, status_code=201)
async def create_screener(
    body: ScreenerCreate,
    session: AsyncSession = Depends(get_session),
) -> ScreenerResponse:
    """Add a new Chartlink screener configuration."""
    screener = Screener(name=body.name, scan_clause=body.scan_clause)
    session.add(screener)
    await session.commit()
    await session.refresh(screener)

    return ScreenerResponse(
        id=screener.id,
        name=screener.name,
        scan_clause=screener.scan_clause,
        is_active=screener.is_active,
    )


@router.patch("/{screener_id}", response_model=ScreenerResponse)
async def update_screener(
    screener_id: int,
    body: ScreenerUpdate,
    session: AsyncSession = Depends(get_session),
) -> ScreenerResponse:
    """Update a screener's name, formula, or active status."""
    stmt = select(Screener).where(Screener.id == screener_id)
    result = await session.exec(stmt)
    screener = result.first()

    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")

    if body.name is not None:
        screener.name = body.name
    if body.scan_clause is not None:
        screener.scan_clause = body.scan_clause
    if body.is_active is not None:
        screener.is_active = body.is_active

    session.add(screener)
    await session.commit()
    await session.refresh(screener)

    return ScreenerResponse(
        id=screener.id,
        name=screener.name,
        scan_clause=screener.scan_clause,
        is_active=screener.is_active,
    )


# ── Manual trigger endpoints ────────────────────────────────────────────

@router.post("/{screener_id}/run", response_model=RunResult)
async def run_screener(
    screener_id: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> RunResult:
    """Manually run a screener NOW (bypasses the 6:30 PM schedule).

    Pipeline:
    1. Fetch stocks from Chartlink via POST simulation.
    2. Upsert stocks + daily snapshots.
    3. Generate tags via Gemini (with caching).
    """
    stmt = select(Screener).where(Screener.id == screener_id)
    result = await session.exec(stmt)
    screener = result.first()

    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")

    settings = get_settings()
    scraper = ChartlinkScraper()

    try:
        scraped = await scraper.run_screener(screener.scan_clause)
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Chartlink scrape failed: {e}"
        ) from e
    finally:
        await scraper.close()

    today = date.today()
    tagged_count = 0

    for stock_data in scraped:
        if not stock_data.symbol:
            continue

        # Upsert stock.
        stock_stmt = select(Stock).where(Stock.symbol == stock_data.symbol)
        stock_result = await session.exec(stock_stmt)
        stock = stock_result.first()

        if not stock:
            stock = Stock(symbol=stock_data.symbol, name=stock_data.name)
            session.add(stock)
            await session.flush()

        # Upsert snapshot.
        snap_stmt = select(DailySnapshot).where(
            DailySnapshot.stock_id == stock.id,
            DailySnapshot.screener_id == screener.id,
            DailySnapshot.snapshot_date == today,
        )
        snap_result = await session.exec(snap_stmt)
        existing = snap_result.first()

        if existing:
            existing.ltp = stock_data.ltp
            existing.volume = stock_data.volume
            existing.change_pct = stock_data.change_pct
            existing.raw_data = stock_data.raw
            session.add(existing)
        else:
            session.add(
                DailySnapshot(
                    stock_id=stock.id,
                    screener_id=screener.id,
                    ltp=stock_data.ltp,
                    volume=stock_data.volume,
                    change_pct=stock_data.change_pct,
                    snapshot_date=today,
                    raw_data=stock_data.raw,
                )
            )

        # Tagging is deferred to the background task

    await session.commit()

    # Queue the background tagging task
    background_tasks.add_task(
        _tag_stocks_in_background,
        scraped_stocks=scraped,
        screener_name=screener.name,
        screener_id=screener.id
    )

    return RunResult(
        screener=screener.name,
        stocks_fetched=len(scraped),
        stocks_tagged=0,  # Tags will be generated asynchronously
        message=f"Screener '{screener.name}' completed. Background tagging started.",
    )


@router.post("/{screener_id}/upload", response_model=RunResult)
async def upload_csv(
    screener_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Chartlink CSV export"),
    session: AsyncSession = Depends(get_session),
) -> RunResult:
    """Upload a Chartlink CSV export — fallback when POST simulation breaks.

    Same pipeline as /run, but reads from uploaded CSV instead of scraping.
    """
    stmt = select(Screener).where(Screener.id == screener_id)
    result = await session.exec(stmt)
    screener = result.first()

    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")

    # Read CSV content.
    content = await file.read()
    csv_text = content.decode("utf-8")

    # Parse CSV using the scraper's static method.
    scraped = ChartlinkScraper.parse_csv(csv_text)

    # Removed tagger init from here

    today = date.today()
    tagged_count = 0

    for stock_data in scraped:
        if not stock_data.symbol:
            continue

        # Upsert stock.
        stock_stmt = select(Stock).where(Stock.symbol == stock_data.symbol)
        stock_result = await session.exec(stock_stmt)
        stock = stock_result.first()

        if not stock:
            stock = Stock(symbol=stock_data.symbol, name=stock_data.name)
            session.add(stock)
            await session.flush()

        # Save snapshot.
        session.add(
            DailySnapshot(
                stock_id=stock.id,
                screener_id=screener.id,
                ltp=stock_data.ltp,
                volume=stock_data.volume,
                change_pct=stock_data.change_pct,
                snapshot_date=today,
                raw_data=stock_data.raw,
            )
        )

        # Tagging is deferred to the background task

    await session.commit()

    # Queue the background tagging task
    background_tasks.add_task(
        _tag_stocks_in_background,
        scraped_stocks=scraped,
        screener_name=screener.name,
        screener_id=screener.id
    )

    return RunResult(
        screener=screener.name,
        stocks_fetched=len(scraped),
        stocks_tagged=0,
        message=f"CSV upload for '{screener.name}' processed. Background tagging started.",
    )
