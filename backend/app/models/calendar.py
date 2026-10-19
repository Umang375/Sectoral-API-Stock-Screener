"""Database model for Indian stock market trading holidays."""

from datetime import date
from sqlmodel import Field, SQLModel


class MarketHoliday(SQLModel, table=True):
    """Stores official exchange trading holidays for NSE and BSE equities."""

    __tablename__ = "market_holidays"

    id: int | None = Field(default=None, primary_key=True)
    holiday_date: date = Field(unique=True, index=True, description="Market holiday date")
    description: str = Field(description="Name/reason of the holiday (e.g. Republic Day, Holi)")
    holiday_type: str = Field(default="TRADING_HOLIDAY", description="Holiday type from exchange (TRADING_HOLIDAY)")
    closed_exchanges: str = Field(default="NSE,BSE", description="Comma-separated list of closed exchanges")
    year: int = Field(index=True, description="Calendar year of holiday")
