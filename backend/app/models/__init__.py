"""Database models barrel-export.

WHY import all models here?
- SQLAlchemy / SQLModel registers tables on the shared `SQLModel.metadata`
  only when the model class is *imported*.  If a model is never imported,
  `create_all()` and Alembic won't see its table.
- By importing everything here, any code that does `from app.models import ...`
  guarantees all tables are registered.
"""

from app.models.screener import Screener  # noqa: F401
from app.models.stock import DailySnapshot, Stock  # noqa: F401
from app.models.tag import StockTag, Tag  # noqa: F401
from app.models.returns import TagWeeklyReturns, WeeklyReturns  # noqa: F401
from app.models.webhook import WebhookAlert  # noqa: F401
