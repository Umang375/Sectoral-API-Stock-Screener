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

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.stock import DailySnapshot, Stock
from app.models.tag import StockTag, Tag
from app.schemas.stock import SnapshotResponse, StockListItem, StockResponse
from app.schemas.tag import StockReturnsItem
from app.models.returns import WeeklyReturns

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("", response_model=list[StockListItem])
async def list_stocks(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
) -> list[StockListItem]:
    """List all tracked stocks with latest LTP and tags.

    Paginated — defaults to 50 items per page, max 200.
    """
    # Fetch stocks with pagination.
    stmt = select(Stock).order_by(Stock.symbol).offset(skip).limit(limit)
    result = await session.exec(stmt)
    stocks = list(result.all())

    items: list[StockListItem] = []
    for stock in stocks:
        # Get latest snapshot for this stock.
        snap_stmt = (
            select(DailySnapshot)
            .where(DailySnapshot.stock_id == stock.id)
            .order_by(DailySnapshot.snapshot_date.desc())
            .limit(1)
        )
        snap_result = await session.exec(snap_stmt)
        latest = snap_result.first()

        # Get tags for this stock.
        tag_stmt = (
            select(Tag.label)
            .join(StockTag, StockTag.tag_id == Tag.id)
            .where(StockTag.stock_id == stock.id)
        )
        tag_result = await session.exec(tag_stmt)
        tags = list(tag_result.all())

        items.append(
            StockListItem(
                symbol=stock.symbol,
                name=stock.name,
                sector=stock.sector,
                tags=tags,
                ltp=latest.ltp if latest else None,
                change_pct=latest.change_pct if latest else None,
            )
        )

    return items


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
