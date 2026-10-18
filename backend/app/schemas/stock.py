"""Pydantic schemas for Stock API responses.

WHY separate schemas from SQLModel models?
─────────────────────────────────────────
SQLModel classes map 1:1 to database tables.  API responses often need a
DIFFERENT shape:

  DB:  Stock(id, symbol, name, sector, first_seen)
  API: StockResponse(symbol, name, sector, tags=["auto ancillaries", ...],
                     latest_snapshot={ltp: 2850, ...})

The API response includes joined/aggregated data that doesn't live in one table.
Pydantic schemas define that "view" shape without polluting the DB model.
"""

from datetime import date, datetime

from pydantic import BaseModel


class SnapshotResponse(BaseModel):
    """A single daily snapshot in API responses."""
    ltp: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    change_pct: float | None = None
    date: date


class StockResponse(BaseModel):
    """Stock detail response — includes tags and latest snapshot."""
    id: int
    symbol: str
    name: str
    sector: str | None = None
    is_active: bool = True
    last_activated_at: date | None = None
    tags: list[str] = []
    latest_snapshot: SnapshotResponse | None = None


class StockListItem(BaseModel):
    """Stock item for list and heatmap matrix endpoints."""
    symbol: str
    name: str
    sector: str | None = None
    is_active: bool = True

    tags: list[str] = []
    ltp: float | None = None
    change_pct: float | None = None
    drawdown_52w_high: float | None = None
    return_1d: float | None = None
    return_1w: float | None = None
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None
    return_2y: float | None = None
    volume: int | None = None

