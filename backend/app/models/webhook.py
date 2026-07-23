"""WebhookAlert model — intraday events from Chartlink alerts.

Design decisions:
─────────────────
WHY a separate alerts table?
- Alerts are EVENT data (something happened at a point in time), while
  snapshots are STATE data (what the stock looked like at market close).
- Alerts fire multiple times per day during market hours; snapshots are daily.
- Different query patterns: "show me all alerts for RELIANCE today" vs
  "show me RELIANCE's closing price last 5 days".

WHY JSONB for payload?
- Chartlink's webhook payload format may change without notice.
- Storing the raw payload means we never lose data, even if our parser
  doesn't handle a new field yet.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class WebhookAlert(SQLModel, table=True):
    """An intraday alert event received from a Chartlink webhook."""

    __tablename__ = "webhook_alerts"

    id: int | None = Field(default=None, primary_key=True)
    stock_id: int = Field(foreign_key="stocks.id", index=True)

    alert_type: str = Field(
        max_length=100,
        description="e.g. '200_DMA_CROSSOVER', 'RSI_OVERBOUGHT'",
    )
    metric: str | None = Field(
        default=None,
        max_length=100,
        description="e.g. '200 DMA', 'RSI'",
    )
    trigger_value: float | None = Field(
        default=None,
        description="Numeric value at which the alert fired",
    )
    payload: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Full webhook payload from Chartlink",
    )
    triggered_at: datetime = Field(
        index=True,
        description="When the alert triggered",
    )
