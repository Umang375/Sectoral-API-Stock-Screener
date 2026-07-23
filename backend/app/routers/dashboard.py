"""Dashboard API router — aggregated summary for the frontend homepage.

WHY a dedicated dashboard endpoint instead of making the frontend call
multiple endpoints and stitching data together?
- Fewer HTTP round-trips: 1 request vs 4 separate requests.
- The backend can optimise the queries (parallel execution, pre-computed data).
- Frontend stays dumb and fast — just renders what it receives.

This is the BFF (Backend For Frontend) pattern applied to a single endpoint.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.returns import TagWeeklyReturns, WeeklyReturns
from app.models.stock import DailySnapshot, Stock
from app.models.tag import StockTag, Tag
from app.models.webhook import WebhookAlert
from app.schemas.returns import (
    DashboardAlert,
    DashboardResponse,
    DashboardStock,
    DashboardTag,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    session: AsyncSession = Depends(get_session),
) -> DashboardResponse:
    """Return a single aggregated dashboard summary.

    Includes:
    - Top 10 stocks by weekly return
    - Top 10 tags by average weekly return
    - 5 most recent webhook alerts
    - Total counts
    """
    # ── Top stocks TODAY (by daily change %) ──────────────────────────
    # Find the most recent snapshot date, then get the top 10 gainers.
    latest_date_stmt = select(func.max(DailySnapshot.snapshot_date))
    latest_date_result = await session.exec(latest_date_stmt)
    latest_date = latest_date_result.one()

    top_stocks_today: list[DashboardStock] = []
    if latest_date:
        daily_stmt = (
            select(Stock.symbol, DailySnapshot.change_pct)
            .join(Stock, Stock.id == DailySnapshot.stock_id)
            .where(DailySnapshot.snapshot_date == latest_date)
            .where(DailySnapshot.change_pct.is_not(None))
            .order_by(DailySnapshot.change_pct.desc())
            .limit(10)
        )
        daily_result = await session.exec(daily_stmt)
        daily_rows = list(daily_result.all())

        for row in daily_rows:
            tag_stmt = (
                select(Tag.label)
                .join(StockTag, StockTag.tag_id == Tag.id)
                .join(Stock, Stock.id == StockTag.stock_id)
                .where(Stock.symbol == row[0])
            )
            tag_result = await session.exec(tag_stmt)
            tags = list(tag_result.all())
            top_stocks_today.append(
                DashboardStock(symbol=row[0], return_pct=row[1], tags=tags)
            )

    # ── Top stocks this week (by return %) ───────────────────────────────
    top_stocks_stmt = (
        select(Stock.symbol, WeeklyReturns.return_pct)
        .join(Stock, Stock.id == WeeklyReturns.stock_id)
        .order_by(WeeklyReturns.week_start.desc(), WeeklyReturns.return_pct.desc())
        .limit(10)
    )
    top_stocks_result = await session.exec(top_stocks_stmt)
    top_stocks_rows = list(top_stocks_result.all())

    top_stocks: list[DashboardStock] = []
    for row in top_stocks_rows:
        # Get tags for this stock.
        tag_stmt = (
            select(Tag.label)
            .join(StockTag, StockTag.tag_id == Tag.id)
            .join(Stock, Stock.id == StockTag.stock_id)
            .where(Stock.symbol == row[0])
        )
        tag_result = await session.exec(tag_stmt)
        tags = list(tag_result.all())

        top_stocks.append(
            DashboardStock(symbol=row[0], return_pct=row[1], tags=tags)
        )

    # ── Top tags this week (by avg return %) ─────────────────────────────
    top_tags_stmt = (
        select(Tag.label, TagWeeklyReturns.avg_return_pct, TagWeeklyReturns.stock_count)
        .join(Tag, Tag.id == TagWeeklyReturns.tag_id)
        .order_by(
            TagWeeklyReturns.week_start.desc(),
            TagWeeklyReturns.avg_return_pct.desc(),
        )
        .limit(10)
    )
    top_tags_result = await session.exec(top_tags_stmt)
    top_tags_rows = list(top_tags_result.all())

    top_tags = [
        DashboardTag(tag=row[0], avg_return_pct=row[1], stock_count=row[2])
        for row in top_tags_rows
    ]

    # ── Recent alerts ────────────────────────────────────────────────────
    alerts_stmt = (
        select(Stock.symbol, WebhookAlert.alert_type, WebhookAlert.triggered_at)
        .join(Stock, Stock.id == WebhookAlert.stock_id)
        .order_by(WebhookAlert.triggered_at.desc())
        .limit(5)
    )
    alerts_result = await session.exec(alerts_stmt)
    alerts_rows = list(alerts_result.all())

    recent_alerts = [
        DashboardAlert(
            stock=row[0],
            alert_type=row[1],
            time=row[2].strftime("%Y-%m-%d %H:%M") if isinstance(row[2], datetime) else str(row[2]),
        )
        for row in alerts_rows
    ]

    # ── Counts ───────────────────────────────────────────────────────────
    stock_count_result = await session.exec(select(func.count(Stock.id)))
    total_stocks = stock_count_result.one()

    tag_count_result = await session.exec(select(func.count(Tag.id)))
    total_tags = tag_count_result.one()

    return DashboardResponse(
        top_stocks_today=top_stocks_today,
        top_stocks_this_week=top_stocks,
        top_tags_this_week=top_tags,
        recent_alerts=recent_alerts,
        total_stocks_tracked=total_stocks,
        total_tags=total_tags,
    )
