"""Tag API router — browse tags and view per-tag returns.

WHY a separate tags router?
- Tags are a first-class entity in our system — not just metadata on stocks.
- Users browse tags to answer "how is the auto ancillaries sector doing?"
- The returns endpoint aggregates across all stocks in a tag cohort.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.returns import TagDailyReturns, TagWeeklyReturns
from app.models.stock import DailySnapshot, Stock
from app.models.tag import StockTag, Tag
from app.schemas.tag import (
    TagDailyReturnsItem,
    TagDailyReturnsResponse,
    TagReturnsItem,
    TagReturnsResponse,
    TagResponse,
    TagStockItem,
)

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def list_tags(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[TagResponse]:
    """List all tags with their stock counts, sorted by popularity.

    WHY sort by stock count?
    - The most useful tags are the most common ones.
    - Rare tags with 1 stock are less interesting for sector analysis.
    """
    # Subquery: count stocks per tag.
    count_subq = (
        select(StockTag.tag_id, func.count(StockTag.stock_id).label("stock_count"))
        .group_by(StockTag.tag_id)
        .subquery()
    )

    stmt = (
        select(Tag.id, Tag.label, func.coalesce(count_subq.c.stock_count, 0).label("stock_count"))
        .outerjoin(count_subq, Tag.id == count_subq.c.tag_id)
        .order_by(func.coalesce(count_subq.c.stock_count, 0).desc())
        .offset(skip)
        .limit(limit)
    )

    result = await session.exec(stmt)
    rows = list(result.all())

    return [
        TagResponse(id=row[0], label=row[1], stock_count=row[2])
        for row in rows
    ]


@router.get("/{label}", response_model=TagResponse)
async def get_tag(
    label: str,
    session: AsyncSession = Depends(get_session),
) -> TagResponse:
    """Get a single tag with its stock count."""
    stmt = select(Tag).where(Tag.label == label.lower())
    result = await session.exec(stmt)
    tag = result.first()

    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag '{label}' not found")

    # Count stocks.
    count_stmt = (
        select(func.count(StockTag.stock_id))
        .where(StockTag.tag_id == tag.id)
    )
    count_result = await session.exec(count_stmt)
    stock_count = count_result.one()

    return TagResponse(id=tag.id, label=tag.label, stock_count=stock_count)


@router.get("/{label}/returns", response_model=TagReturnsResponse)
async def get_tag_returns(
    label: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(12, ge=1, le=52, description="Number of weeks"),
) -> TagReturnsResponse:
    """Get weekly aggregated returns for a tag cohort.

    Shows how stocks in this sector performed week over week.
    """
    stmt = select(Tag).where(Tag.label == label.lower())
    result = await session.exec(stmt)
    tag = result.first()

    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag '{label}' not found")

    returns_stmt = (
        select(TagWeeklyReturns)
        .where(TagWeeklyReturns.tag_id == tag.id)
        .order_by(TagWeeklyReturns.week_start.desc())
        .limit(limit)
    )
    returns_result = await session.exec(returns_stmt)
    returns = list(returns_result.all())

    items: list[TagReturnsItem] = []
    for row in returns:
        points_result = await session.exec(
            select(func.count(func.distinct(DailySnapshot.snapshot_date)))
            .join(StockTag, StockTag.stock_id == DailySnapshot.stock_id)
            .where(
                StockTag.tag_id == tag.id,
                DailySnapshot.snapshot_date >= row.week_start,
                DailySnapshot.snapshot_date <= row.week_end,
            )
        )
        data_points = points_result.one()
        items.append(
            TagReturnsItem(
                week_start=row.week_start,
                week_end=row.week_end,
                avg_return_pct=row.avg_return_pct,
                median_return_pct=row.median_return_pct,
                stock_count=row.stock_count,
                data_points=data_points,
                is_complete=data_points >= 5,
            )
        )

    return TagReturnsResponse(tag=tag.label, returns=items)


@router.get("/{label}/stocks", response_model=list[TagStockItem])
async def get_tag_stocks(
    label: str,
    session: AsyncSession = Depends(get_session),
) -> list[TagStockItem]:
    """Get stocks currently associated with a tag."""
    tag_result = await session.exec(select(Tag).where(Tag.label == label.lower()))
    tag = tag_result.first()
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag '{label}' not found")

    stmt = (
        select(Stock)
        .join(StockTag, StockTag.stock_id == Stock.id)
        .where(StockTag.tag_id == tag.id)
        .order_by(Stock.symbol)
    )
    stocks_result = await session.exec(stmt)
    items: list[TagStockItem] = []
    for stock in stocks_result.all():
        snapshot_result = await session.exec(
            select(DailySnapshot)
            .where(DailySnapshot.stock_id == stock.id)
            .order_by(DailySnapshot.snapshot_date.desc())
            .limit(1)
        )
        latest = snapshot_result.first()
        items.append(
            TagStockItem(
                symbol=stock.symbol,
                name=stock.name,
                ltp=latest.ltp if latest else None,
                change_pct=latest.change_pct if latest else None,
            )
        )
    return items


@router.get("/{label}/daily-returns", response_model=TagDailyReturnsResponse)
async def get_tag_daily_returns(
    label: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(30, ge=1, le=90, description="Number of trading days"),
) -> TagDailyReturnsResponse:
    """Get end-of-day sector performance history for a tag."""
    tag_stmt = select(Tag).where(Tag.label == label.lower())
    tag_result = await session.exec(tag_stmt)
    tag = tag_result.first()
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag '{label}' not found")

    returns_stmt = (
        select(TagDailyReturns)
        .where(TagDailyReturns.tag_id == tag.id)
        .order_by(TagDailyReturns.snapshot_date.desc())
        .limit(limit)
    )
    returns_result = await session.exec(returns_stmt)
    return TagDailyReturnsResponse(
        tag=tag.label,
        returns=[
            TagDailyReturnsItem(
                snapshot_date=row.snapshot_date,
                avg_return_pct=row.avg_return_pct,
                median_return_pct=row.median_return_pct,
                stock_count=row.stock_count,
                advancing_count=row.advancing_count,
                declining_count=row.declining_count,
            )
            for row in returns_result.all()
        ],
    )
