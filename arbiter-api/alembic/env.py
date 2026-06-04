from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

import os
import sys

if os.environ.get("ALEMBIC_ALLOW_DOWNGRADE") != "true" and any(arg.startswith("downgrade") for arg in sys.argv):
    sys.stderr.write("DOWNGRADE REJECTED in production. Set ALEMBIC_ALLOW_DOWNGRADE=true to override.\n")
    sys.exit(1)

from app.core.config import settings
from app.core.database import Base
from app.models.alert import Alert
from app.models.dag_definition import DagDefinition
from app.models.organization import Organization
from app.models.pipeline import Pipeline
from app.models.pipeline_run import PipelineRun
from app.models.task_instance import TaskInstance

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())