"""Screener model — stores Chartlink scan configurations.

Each screener row represents a saved Chartlink scan formula (scan_clause).
The system runs active screeners daily at 6:30 PM IST to fetch matching stocks.

WHY a separate Screener table?
- You might run multiple screeners (e.g., "Volume Breakouts", "52-week Highs").
- Each screener produces different stock lists, so snapshots and tags need to
  know WHICH screener found them.
- The scan_clause is the raw Chartlink formula — keeping it in the DB means
  you can add/modify screeners without redeploying code.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Screener(SQLModel, table=True):
    """A Chartlink screener configuration."""

    __tablename__ = "screeners"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, description="Human-readable screener name")
    scan_clause: str = Field(description="Chartlink scan formula")
    is_active: bool = Field(default=True, description="Whether to run daily")
    created_at: datetime = Field(default_factory=datetime.utcnow)
