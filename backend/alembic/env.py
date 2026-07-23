"""Alembic environment configuration — bridges Alembic with our app.

KEY DESIGN DECISIONS:
─────────────────────
1. We import SQLModel.metadata as the target_metadata so Alembic can
   auto-detect schema changes by comparing our models to the actual DB.
2. We read DATABASE_URL from our Pydantic Settings (not from alembic.ini)
   so there's a SINGLE source of truth for the connection string.
3. We use run_migrations_online() for async support — Alembic runs
   migrations through an async engine, matching our app's architecture.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine
from sqlmodel import SQLModel

# Import all models so they register on SQLModel.metadata.
import app.models  # noqa: F401
from app.config import get_settings

# Alembic Config object — provides access to alembic.ini values.
config = context.config

# Set up Python logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object that Alembic compares against the live DB.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL without connecting.

    Useful for generating migration SQL scripts to review before applying.
    """
    settings = get_settings()
    url = settings.DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations using the provided connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations through an async engine."""
    settings = get_settings()
    connectable = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the DB and applies changes."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
