"""Stock API router — CRUD and history for tracked stocks.

PATTERN: Thin Router
────────────────────
Each endpoint does exactly 3 things:
1. Parse the request (path/query params, validated by FastAPI automatically).
2. Run a database query via the injected AsyncSession.
3. Return a Pydantic schema (FastAPI serialises it to JSON).

No business logic here — if we needed complex stock analysis, it would
live in a service.  Routers are the HTTP "skin" of the application.

WHY Depends(get_session)?
- Each request gets its own DB session (transaction isolation).
- FastAPI auto-closes the session when the response is sent.
- In tests, you override get_session to inject a test DB.
"""

from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.constants.sectors import PREDEFINED_SECTORS
from app.database import get_session
from app.models.stock import DailySnapshot, Stock
from app.models.tag import StockTag, Tag
from app.schemas.stock import SnapshotResponse, StockListItem, StockResponse
from app.schemas.tag import StockReturnsItem
from app.models.returns import WeeklyReturns

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


class SectorSummary(BaseModel):
    """Summary of stocks classified under a predefined sector."""
    name: str
    stock_count: int



@router.get("", response_model=list[StockListItem])
async def list_stocks(
    session: AsyncSession = Depends(get_session),
    sector: str | None = Query(None, description="Filter stocks by classified sector"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=200, description="Page size"),
) -> list[StockListItem]:
    """List all tracked stocks with latest LTP, tags, and multi-period performance matrix."""
    # Fetch stocks with pagination and optional sector filter.
    stmt = select(Stock)
    if sector:
        stmt = stmt.where(func.lower(Stock.sector) == sector.lower().strip())
    stmt = stmt.order_by(Stock.symbol).offset(skip).limit(limit)
    result = await session.exec(stmt)
    stocks = list(result.all())

    if not stocks:
        return []

    stock_ids = [s.id for s in stocks]

    # Fetch tags for all these stocks in one query
    tag_stmt = (
        select(StockTag.stock_id, Tag.label)
        .join(Tag, Tag.id == StockTag.tag_id)
        .where(StockTag.stock_id.in_(stock_ids))
    )
    tag_result = await session.exec(tag_stmt)
    tags_by_stock: dict[int, list[str]] = defaultdict(list)
    for sid, lbl in tag_result.all():
        tags_by_stock[sid].append(lbl)

    # Fetch all snapshots for these stocks in one query
    snap_stmt = (
        select(DailySnapshot)
        .where(DailySnapshot.stock_id.in_(stock_ids))
        .order_by(DailySnapshot.snapshot_date.desc())
    )
    snap_res = await session.exec(snap_stmt)
    snaps_by_stock: dict[int, list[DailySnapshot]] = defaultdict(list)
    for s in snap_res.all():
        snaps_by_stock[s.stock_id].append(s)

    items: list[StockListItem] = []
    for stock in stocks:
        snaps = snaps_by_stock.get(stock.id, [])
        tags = tags_by_stock.get(stock.id, [])

        if not snaps:
            items.append(
                StockListItem(
                    symbol=stock.symbol,
                    name=stock.name,
                    sector=stock.sector,
                    tags=tags,
                )
            )
            continue

        latest_snap = snaps[0]
        ref_date = latest_snap.snapshot_date
        valid_ltps = [s.ltp for s in snaps if s.ltp is not None]
        max_ltp = max(valid_ltps) if valid_ltps else None

        drawdown_52w = (
            round(((latest_snap.ltp - max_ltp) / max_ltp) * 100, 1)
            if (latest_snap.ltp is not None and max_ltp and max_ltp > 0)
            else None
        )

        def get_anchor_ltp(target_days: int, min_days: int, max_days: int) -> float | None:
            candidates = [
                s for s in snaps
                if s.ltp is not None and min_days <= (ref_date - s.snapshot_date).days <= max_days
            ]
            if not candidates:
                return None
            target_d = ref_date - timedelta(days=target_days)
            candidates.sort(key=lambda s: abs((s.snapshot_date - target_d).days))
            return candidates[0].ltp

        def calc_ret(past_val: float | None) -> float | None:
            if latest_snap.ltp is not None and past_val is not None and past_val > 0:
                return round(((latest_snap.ltp - past_val) / past_val) * 100, 2)
            return None

        ret_1w = calc_ret(get_anchor_ltp(7, 4, 12))
        ret_1m = calc_ret(get_anchor_ltp(30, 20, 45))
        ret_3m = calc_ret(get_anchor_ltp(90, 65, 115))
        ret_6m = calc_ret(get_anchor_ltp(180, 140, 220))
        ret_1y = calc_ret(get_anchor_ltp(365, 300, 420))
        ret_2y = calc_ret(get_anchor_ltp(730, 650, 800))

        items.append(
            StockListItem(
                symbol=stock.symbol,
                name=stock.name,
                sector=stock.sector,
                tags=tags,
                ltp=latest_snap.ltp,
                change_pct=latest_snap.change_pct,
                drawdown_52w_high=drawdown_52w,
                return_1d=latest_snap.change_pct,
                return_1w=ret_1w,
                return_1m=ret_1m,
                return_3m=ret_3m,
                return_6m=ret_6m,
                return_1y=ret_1y,
                return_2y=ret_2y,
                volume=latest_snap.volume,
            )
        )

    return items


@router.get("/sectors", response_model=list[SectorSummary])
async def list_sectors(
    session: AsyncSession = Depends(get_session),
) -> list[SectorSummary]:
    """List predefined sectors with current stock counts."""
    stmt = (
        select(Stock.sector, func.count(Stock.id))
        .where(Stock.sector.is_not(None))
        .group_by(Stock.sector)
    )
    result = await session.exec(stmt)
    counts = {s: c for s, c in result.all() if s}

    summaries = [
        SectorSummary(name=sec, stock_count=counts.get(sec, 0))
        for sec in PREDEFINED_SECTORS
    ]
    summaries.sort(key=lambda x: (-x.stock_count, x.name))
    return summaries


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str,
    session: AsyncSession = Depends(get_session),
) -> StockResponse:
    """Get detailed info for a single stock, including tags and latest snapshot."""
    stmt = select(Stock).where(Stock.symbol == symbol.upper())
    result = await session.exec(stmt)
    stock = result.first()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")

    # Latest snapshot.
    snap_stmt = (
        select(DailySnapshot)
        .where(DailySnapshot.stock_id == stock.id)
        .order_by(DailySnapshot.snapshot_date.desc())
        .limit(1)
    )
    snap_result = await session.exec(snap_stmt)
    latest = snap_result.first()

    # Tags.
    tag_stmt = (
        select(Tag.label)
        .join(StockTag, StockTag.tag_id == Tag.id)
        .where(StockTag.stock_id == stock.id)
    )
    tag_result = await session.exec(tag_stmt)
    tags = list(tag_result.all())

    return StockResponse(
        id=stock.id,
        symbol=stock.symbol,
        name=stock.name,
        sector=stock.sector,
        tags=tags,
        latest_snapshot=(
            SnapshotResponse(
                ltp=latest.ltp,
                volume=latest.volume,
                change_pct=latest.change_pct,
                date=latest.snapshot_date,
            )
            if latest
            else None
        ),
    )


@router.get("/{symbol}/history", response_model=list[SnapshotResponse])
async def get_stock_history(
    symbol: str,
    session: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=365),
) -> list[SnapshotResponse]:
    """Get daily snapshot history for a stock (newest first)."""
    stock_stmt = select(Stock).where(Stock.symbol == symbol.upper())
    stock_result = await session.exec(stock_stmt)
    stock = stock_result.first()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")

    stmt = (
        select(DailySnapshot)
        .where(DailySnapshot.stock_id == stock.id)
        .order_by(DailySnapshot.snapshot_date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(stmt)
    snapshots = list(result.all())

    return [
        SnapshotResponse(
            ltp=s.ltp,
            volume=s.volume,
            change_pct=s.change_pct,
            date=s.snapshot_date,
        )
        for s in snapshots
    ]


@router.get("/{symbol}/returns", response_model=list[StockReturnsItem])
async def get_stock_returns(
    symbol: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(12, ge=1, le=52, description="Number of weeks"),
) -> list[StockReturnsItem]:
    """Get weekly returns history for a stock (newest first)."""
    stock_stmt = select(Stock).where(Stock.symbol == symbol.upper())
    stock_result = await session.exec(stock_stmt)
    stock = stock_result.first()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")

    stmt = (
        select(WeeklyReturns)
        .where(WeeklyReturns.stock_id == stock.id)
        .order_by(WeeklyReturns.week_start.desc())
        .limit(limit)
    )
    result = await session.exec(stmt)
    returns = list(result.all())

    return [
        StockReturnsItem(
            week_start=r.week_start,
            week_end=r.week_end,
            open_ltp=r.open_ltp,
            close_ltp=r.close_ltp,
            return_pct=r.return_pct,
        )
        for r in returns
    ]
