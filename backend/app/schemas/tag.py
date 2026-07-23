"""Pydantic schemas for Tag and Returns API responses."""

from datetime import date

from pydantic import BaseModel


class TagResponse(BaseModel):
    """A tag with its stock count."""
    id: int
    label: str
    stock_count: int = 0


class TagReturnsItem(BaseModel):
    """One week's aggregated return for a tag cohort."""
    week_start: date
    week_end: date
    avg_return_pct: float
    median_return_pct: float
    stock_count: int


class TagReturnsResponse(BaseModel):
    """Full returns history for a tag."""
    tag: str
    returns: list[TagReturnsItem] = []


class StockReturnsItem(BaseModel):
    """One week's return for a single stock."""
    week_start: date
    week_end: date
    open_ltp: float
    close_ltp: float
    return_pct: float
