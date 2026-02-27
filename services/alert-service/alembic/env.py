"""Alembic environment configuration for async SQLAlchemy.

This ``env.py`` supports both offline (SQL script generation) and online
(live database connection) migration modes using ``asyncpg``.

It imports the application's ``Base.metadata`` so that ``--autogenerate``
can compare the ORM models against the actual database schema.
"""
from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that ``src.*`` imports work.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import *after* path adjustment.
from src.infrastructure.persistence.database import Base  # noqa: E402
from src.infrastructure.persistence.models import ViolationModel, AlertConfigModel  # noqa: E402, F401

# ---------------------------------------------------------------------------
# Alembic Config object — provides access to alembic.ini values.
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url from environment if available.
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aqms_user:aqms_pass@localhost:5434/alert_db",
)
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The metadata object used by --autogenerate.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode — generates SQL scripts without a live connection.
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    Calls to ``context.execute()`` emit the given string to the script
    output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — runs migrations against a live async database.
# ---------------------------------------------------------------------------
def do_run_migrations(connection):
    """Run migrations with the provided connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point — select mode based on context.
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
