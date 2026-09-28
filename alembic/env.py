"""Alembic environment for AgriN.

The database URL is taken from the application's typed ``Settings`` (env/.env),
never hardcoded in ``alembic.ini``. ``target_metadata`` is the shared
``Base.metadata`` so future ``--autogenerate`` revisions see all models.
"""

from __future__ import annotations

import asyncio
from typing import Literal

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.sql.schema import SchemaItem
from src.core.config import get_settings

# Importing the package (not base directly) registers every model on
# Base.metadata so `alembic revision --autogenerate` sees all tables.
from src.models import Base

config = context.config

# NOTE (M009 finding): stock alembic env.py calls
# `fileConfig(config.config_file_name)` here. Deliberately omitted — it would
# reconfigure the root logger (alembic.ini sets root=WARNING and disables
# existing loggers), which (a) fights the app's JSON logging and (b) broke
# pytest caplog assertions once in-process migrations ran before tests.
# The app configures logging itself (src/core/logging.py).

target_metadata = Base.metadata


def _include_object(
    obj: SchemaItem,
    name: str | None,
    type_: Literal[
        "schema",
        "table",
        "column",
        "index",
        "unique_constraint",
        "foreign_key_constraint",
        "check_constraint",
    ],
    reflected: bool,
    compare_to: SchemaItem | None,
) -> bool:
    """Autogenerate filter (M018 finding): ``spatial_ref_sys`` belongs to the
    PostGIS extension, not to AgriN's models. Without this, ``alembic check``
    and every generated diff report a bogus ``remove_table`` — noise that
    would mask real drift during hand-review (standing rule)."""
    return not (type_ == "table" and name == "spatial_ref_sys")


def _database_url() -> str:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "database_url is not configured; set DATABASE_URL before running migrations."
        )
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no DBAPI)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=_include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=_include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through a sync-bridged connection."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
