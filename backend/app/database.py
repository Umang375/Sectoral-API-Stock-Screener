"""Async database engine and session factory.

WHY async?
- The API is I/O-heavy (DB queries, HTTP calls to Chartlink/Gemini, Redis).
  Async lets a single worker handle many concurrent requests without threads.

WHY SQLModel + AsyncSession?
- SQLModel unifies SQLAlchemy models and Pydantic schemas, reducing boilerplate.
- AsyncSession from sqlmodel.ext.asyncio gives us first-class async/await support
  with the same SQLModel models we already define.

WHY get_session() as an async generator?
- FastAPI's Depends() expects an async generator so it can manage the session
  lifecycle (open → yield → commit/rollback → close) per-request automatically.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
import app.models  # noqa: F401  — registers all tables on SQLModel.metadata

settings = get_settings()

# Pool size tuned for a single-server deployment; bump for production.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    future=True,
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session, then close it.

    Usage in routers:
        @router.get("/items")
        async def list_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Create all tables from SQLModel metadata.

    Intended for development / first-run bootstrapping.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
