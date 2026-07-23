"""Pydantic schemas for Returns / Dashboard API responses."""

from datetime import date

from pydantic import BaseModel


class DashboardStock(BaseModel):
    """Stock summary item for the dashboard."""
    symbol: str
    return_pct: float
    tags: list[str] = []


class DashboardTag(BaseModel):
    """Tag summary item for the dashboard."""
    tag: str
    avg_return_pct: float
    stock_count: int


class DashboardAlert(BaseModel):
    """Recent alert item for the dashboard."""
    stock: str
    alert_type: str
    time: str


class DashboardResponse(BaseModel):
    """Top-level dashboard summary."""
    top_stocks_today: list[DashboardStock] = []
    top_stocks_this_week: list[DashboardStock] = []
    top_tags_this_week: list[DashboardTag] = []
    recent_alerts: list[DashboardAlert] = []
    total_stocks_tracked: int = 0
    total_tags: int = 0
