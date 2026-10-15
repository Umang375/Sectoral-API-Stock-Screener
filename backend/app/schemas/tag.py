"""Pydantic schemas for Tag and Returns API responses."""

from datetime import date

from pydantic import BaseModel


class TagStockDetail(BaseModel):
    """Constituent stock item in sector heatmap matrix."""
    symbol: str
    name: str
    ltp: float | None = None
    change_pct: float | None = None
    drawdown_52w_high: float | None = None
    volume: int | None = None


class TagResponse(BaseModel):
    """A tag with its stock count and multi-period performance matrix."""
    id: int
    label: str
    stock_count: int = 0
    advancing_count: int = 0
    declining_count: int = 0
    unchanged_count: int = 0
    drawdown_52w_high: float | None = None
    return_1d: float | None = None
    return_1w: float | None = None
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None
    return_2y: float | None = None
    stocks: list[TagStockDetail] = []


class TagReturnsItem(BaseModel):
    """One week's aggregated return for a tag cohort."""
    week_start: date
    week_end: date
    avg_return_pct: float
    median_return_pct: float
    stock_count: int
    data_points: int = 0
    is_complete: bool = True


class TagReturnsResponse(BaseModel):
    """Full returns history for a tag."""
    tag: str
    returns: list[TagReturnsItem] = []


class TagDailyReturnsItem(BaseModel):
    """One end-of-day aggregate return for a tag cohort."""
    snapshot_date: date
    avg_return_pct: float
    median_return_pct: float
    stock_count: int
    advancing_count: int
    declining_count: int


class TagDailyReturnsResponse(BaseModel):
    """Daily sector performance history for a tag."""
    tag: str
    returns: list[TagDailyReturnsItem] = []


class TagStockItem(BaseModel):
    """A stock currently associated with a tag."""
    symbol: str
    name: str
    ltp: float | None = None
    change_pct: float | None = None


class StockReturnsItem(BaseModel):
    """One week's return for a single stock."""
    week_start: date
    week_end: date
    open_ltp: float
    close_ltp: float
    return_pct: float
