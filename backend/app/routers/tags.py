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
from app.models.returns import TagWeeklyReturns
from app.models.tag import StockTag, Tag
from app.schemas.tag import TagReturnsItem, TagReturnsResponse, TagResponse

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

    return TagReturnsResponse(
        tag=tag.label,
        returns=[
            TagReturnsItem(
                week_start=r.week_start,
                week_end=r.week_end,
                avg_return_pct=r.avg_return_pct,
                median_return_pct=r.median_return_pct,
                stock_count=r.stock_count,
            )
            for r in returns
        ],
    )
