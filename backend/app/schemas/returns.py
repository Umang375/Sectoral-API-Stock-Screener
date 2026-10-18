"""Pydantic schemas for Returns / Dashboard API responses."""

from datetime import date as dt_date

from pydantic import BaseModel


class DashboardStock(BaseModel):
    """Stock summary item for the dashboard."""
    symbol: str
    return_pct: float
    tags: list[str] = []
    data_points: int = 0
    is_complete: bool = True


class DashboardTag(BaseModel):
    """Tag summary item for the dashboard."""
    tag: str
    avg_return_pct: float
    stock_count: int
    data_points: int = 0
    is_complete: bool = True


class DashboardAlert(BaseModel):
    """Recent alert item for the dashboard."""
    stock: str
    alert_type: str
    time: str


class DashboardLifecycleStock(BaseModel):
    """Stock item representing dumped (inactive) or recently added/reactivated equities."""
    symbol: str
    name: str
    sector: str | None = None
    status: str  # "new", "reactivated", or "dumped"
    date: dt_date | None = None
    days_inactive: int | None = None
    ltp: float | None = None


class DashboardResponse(BaseModel):
    """Top-level dashboard summary."""
    top_stocks_today: list[DashboardStock] = []
    top_stocks_this_week: list[DashboardStock] = []
    top_tags_this_week: list[DashboardTag] = []
    top_tags_today: list[DashboardTag] = []
    recent_alerts: list[DashboardAlert] = []
    dumped_stocks: list[DashboardLifecycleStock] = []
    recently_added_stocks: list[DashboardLifecycleStock] = []
    total_stocks_tracked: int = 0
    total_tags: int = 0

