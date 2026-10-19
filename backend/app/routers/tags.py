"""Tag API router — browse tags and view per-tag returns.

WHY a separate tags router?
- Tags are a first-class entity in our system — not just metadata on stocks.
- Users browse tags to answer "how is the auto ancillaries sector doing?"
- The returns endpoint aggregates across all stocks in a tag cohort.
"""

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean

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
    TagStockDetail,
    TagStockItem,
)
from app.services.market_calendar import get_expected_trading_days

router = APIRouter(prefix="/api/tags", tags=["tags"])


async def _enrich_tags_with_metrics(
    session: AsyncSession,
    tag_rows: list[tuple[int, str, int]],
) -> list[TagResponse]:
    """Enrich a list of (tag_id, label, stock_count) with full performance matrix."""
    if not tag_rows:
        return []

    tag_ids = [r[0] for r in tag_rows]

    # 1. Fetch stock mappings for these tags
    stock_tag_stmt = (
        select(StockTag.tag_id, Stock.id, Stock.symbol, Stock.name, Stock.return_2y)
        .join(Stock, Stock.id == StockTag.stock_id)
        .where(StockTag.tag_id.in_(tag_ids))
        .order_by(Stock.symbol)
    )
    stock_tag_result = await session.exec(stock_tag_stmt)
    stock_tag_rows = stock_tag_result.all()

    tag_stocks_map: dict[int, list[tuple[int, str, str]]] = defaultdict(list)
    stock_ret_2y_map: dict[int, float | None] = {}
    all_stock_ids = set()
    for row in stock_tag_rows:
        tag_stocks_map[row[0]].append((row[1], row[2], row[3]))
        stock_ret_2y_map[row[1]] = row[4]
        all_stock_ids.add(row[1])

    # 2. Fetch latest TagDailyReturns & TagWeeklyReturns if available
    daily_returns_stmt = (
        select(TagDailyReturns)
        .where(TagDailyReturns.tag_id.in_(tag_ids))
        .order_by(TagDailyReturns.snapshot_date.desc())
    )
    daily_returns_res = await session.exec(daily_returns_stmt)
    tag_daily_map: dict[int, TagDailyReturns] = {}
    for dr in daily_returns_res.all():
        if dr.tag_id not in tag_daily_map:
            tag_daily_map[dr.tag_id] = dr

    weekly_returns_stmt = (
        select(TagWeeklyReturns)
        .where(TagWeeklyReturns.tag_id.in_(tag_ids))
        .order_by(TagWeeklyReturns.week_start.desc())
    )
    weekly_returns_res = await session.exec(weekly_returns_stmt)
    tag_weekly_map: dict[int, TagWeeklyReturns] = {}
    for wr in weekly_returns_res.all():
        if wr.tag_id not in tag_weekly_map:
            tag_weekly_map[wr.tag_id] = wr

    # 3. Fetch snapshots for constituent stocks
    stock_metrics: dict[int, dict] = {}
    if all_stock_ids:
        snap_stmt = (
            select(DailySnapshot)
            .where(DailySnapshot.stock_id.in_(list(all_stock_ids)))
            .order_by(DailySnapshot.snapshot_date.desc())
        )
        snap_res = await session.exec(snap_stmt)
        all_snaps = snap_res.all()

        snaps_by_stock: dict[int, list[DailySnapshot]] = defaultdict(list)
        for s in all_snaps:
            snaps_by_stock[s.stock_id].append(s)

        for stock_id, snaps in snaps_by_stock.items():
            if not snaps:
                continue
            latest_snap = snaps[0]
            ref_date = latest_snap.snapshot_date
            valid_52w_prices = [
                s.high if s.high is not None else s.ltp for s in snaps
                if (s.high is not None or s.ltp is not None)
                and 0 <= (ref_date - s.snapshot_date).days <= 365
            ]
            max_price = max(valid_52w_prices) if valid_52w_prices else None

            drawdown_52w = (
                round(((latest_snap.ltp - max_price) / max_price) * 100, 1)
                if (latest_snap.ltp is not None and max_price and max_price > 0)
                else None
            )

            # Anchor lookups for multi-period returns
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

            stock_metrics[stock_id] = {
                "ltp": latest_snap.ltp,
                "change_pct": latest_snap.change_pct,
                "volume": latest_snap.volume,
                "drawdown_52w": drawdown_52w,
                "ret_1w": calc_ret(get_anchor_ltp(7, 4, 12)),
                "ret_1m": calc_ret(get_anchor_ltp(30, 20, 45)),
                "ret_3m": calc_ret(get_anchor_ltp(90, 65, 115)),
                "ret_6m": calc_ret(get_anchor_ltp(180, 140, 220)),
                "ret_1y": calc_ret(get_anchor_ltp(365, 300, 420)),
                "ret_2y": stock_ret_2y_map.get(stock_id) if stock_ret_2y_map.get(stock_id) is not None else calc_ret(get_anchor_ltp(730, 650, 800)),
            }

    # 4. Construct enriched TagResponse items
    responses: list[TagResponse] = []
    for tag_id, label, count in tag_rows:
        constituent_stocks_info = tag_stocks_map.get(tag_id, [])
        stock_details: list[TagStockDetail] = []

        ret_1w_list = []
        ret_1m_list = []
        ret_3m_list = []
        ret_6m_list = []
        ret_1y_list = []
        ret_2y_list = []
        drawdown_list = []

        for sid, sym, nm in constituent_stocks_info:
            sm = stock_metrics.get(sid, {})
            stock_details.append(
                TagStockDetail(
                    symbol=sym,
                    name=nm,
                    ltp=sm.get("ltp"),
                    change_pct=sm.get("change_pct"),
                    drawdown_52w_high=sm.get("drawdown_52w"),
                    volume=sm.get("volume"),
                )
            )
            if sm.get("drawdown_52w") is not None:
                drawdown_list.append(sm["drawdown_52w"])
            if sm.get("ret_1w") is not None:
                ret_1w_list.append(sm["ret_1w"])
            if sm.get("ret_1m") is not None:
                ret_1m_list.append(sm["ret_1m"])
            if sm.get("ret_3m") is not None:
                ret_3m_list.append(sm["ret_3m"])
            if sm.get("ret_6m") is not None:
                ret_6m_list.append(sm["ret_6m"])
            if sm.get("ret_1y") is not None:
                ret_1y_list.append(sm["ret_1y"])
            if sm.get("ret_2y") is not None:
                ret_2y_list.append(sm["ret_2y"])

        # Advance / Decline / Unchanged & 1D
        if stock_details:
            valid_1d = [s.change_pct for s in stock_details if s.change_pct is not None]
            adv_count = sum(1 for s in stock_details if s.change_pct is not None and s.change_pct > 0)
            dec_count = sum(1 for s in stock_details if s.change_pct is not None and s.change_pct < 0)
            unc_count = sum(1 for s in stock_details if s.change_pct is not None and s.change_pct == 0)
            # Constituents without fresh change_pct count as unchanged so adv + unc + dec == len(stock_details)
            unc_count += sum(1 for s in stock_details if s.change_pct is None)
            ret_1d = round(mean(valid_1d), 1) if valid_1d else None
        elif tag_id in tag_daily_map:
            adv_count = tag_daily_map[tag_id].advancing_count
            dec_count = tag_daily_map[tag_id].declining_count
            unc_count = max(0, tag_daily_map[tag_id].stock_count - adv_count - dec_count)
            ret_1d = round(tag_daily_map[tag_id].avg_return_pct, 1)
        else:
            adv_count = 0
            dec_count = 0
            unc_count = 0
            ret_1d = None

        # 1W
        if ret_1w_list:
            ret_1w = round(mean(ret_1w_list), 1)
        elif tag_id in tag_weekly_map:
            ret_1w = round(tag_weekly_map[tag_id].avg_return_pct, 1)
        else:
            ret_1w = None

        # Multi-period (return None when not enough data)
        ret_1m = round(mean(ret_1m_list), 1) if ret_1m_list else None
        ret_3m = round(mean(ret_3m_list), 1) if ret_3m_list else None
        ret_6m = round(mean(ret_6m_list), 1) if ret_6m_list else None
        ret_1y = round(mean(ret_1y_list), 1) if ret_1y_list else None
        ret_2y = round(mean(ret_2y_list), 1) if ret_2y_list else None
        drawdown_52w_val = round(mean(drawdown_list), 1) if drawdown_list else None

        responses.append(
            TagResponse(
                id=tag_id,
                label=label,
                stock_count=len(stock_details) if stock_details else count,
                advancing_count=adv_count,
                declining_count=dec_count,
                unchanged_count=unc_count,
                drawdown_52w_high=drawdown_52w_val,
                return_1d=ret_1d,
                return_1w=ret_1w,
                return_1m=ret_1m,
                return_3m=ret_3m,
                return_6m=ret_6m,
                return_1y=ret_1y,
                return_2y=ret_2y,
                stocks=stock_details,
            )
        )

    return responses


@router.get("", response_model=list[TagResponse])
async def list_tags(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
) -> list[TagResponse]:
    """List all tags with their performance matrix and constituent stocks."""
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

    return await _enrich_tags_with_metrics(session, rows)


@router.get("/{label}", response_model=TagResponse)
async def get_tag(
    label: str,
    session: AsyncSession = Depends(get_session),
) -> TagResponse:
    """Get a single tag with its performance matrix."""
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

    enriched = await _enrich_tags_with_metrics(session, [(tag.id, tag.label, stock_count)])
    if enriched:
        return enriched[0]

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
        expected_days = get_expected_trading_days(row.week_start, row.week_end)
        items.append(
            TagReturnsItem(
                week_start=row.week_start,
                week_end=row.week_end,
                avg_return_pct=row.avg_return_pct,
                median_return_pct=row.median_return_pct,
                stock_count=row.stock_count,
                data_points=data_points,
                is_complete=data_points >= expected_days,
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
