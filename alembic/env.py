"""Alembic environment configuration."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db import base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = base.metadata


def _configure_url() -> None:
    settings = get_settings()
    config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    _configure_url()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    _configure_url()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


def run_async_migrations_online() -> None:
    """Run migrations in online async mode."""

    from sqlalchemy.ext.asyncio import async_engine_from_config

    _configure_url()
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda sync_connection: context.configure(
                    connection=sync_connection, target_metadata=target_metadata
                )
            )

            await connection.run_sync(lambda _: context.begin_transaction())
            await connection.run_sync(lambda _: context.run_migrations())

    asyncio.run(do_run_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
