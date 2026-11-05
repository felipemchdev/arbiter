"""Adopt a schema that exists without Alembic history so migrations can run.

The seeders build tables with ``Base.metadata.create_all``, which never writes an
``alembic_version`` row. On the next start ``alembic upgrade head`` replays the
initial migration against tables that already exist, the process exits non-zero,
and the container restart policy repeats that failure forever.

The head revision is stamped only when the live schema already holds every model
table, every model column and the uniqueness objects the application relies on.
A partial schema is refused instead: stamping it would tell Alembic the database is
current while a protection that later revisions add - the unique run key or the
active-alert index - is still missing.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.schema import UniqueConstraint

import app.models  # noqa: F401 - registers every table on Base.metadata
from app.core.database import Base, engine

API_ROOT = Path(__file__).resolve().parents[2]


def _script_directory() -> ScriptDirectory:
    """Load the migration scripts by absolute path, so the cwd does not matter."""
    config = Config(str(API_ROOT / "alembic.ini"))
    # alembic.ini predates this option; without it Alembic warns on every boot.
    config.set_main_option("path_separator", "os")
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    return ScriptDirectory.from_config(config)


def _uniqueness_guards(table) -> dict[str, str]:
    """Return the named uniqueness objects a table must carry, by kind.

    Only objects that stop duplicate rows are required. Plain ``ix_*`` indexes are
    performance-only, and a missing one is repaired by ``CREATE INDEX``, not by a
    human decision. Column types stay unchecked: the driver returns dialect objects
    that do not compare reliably between SQLite and PostgreSQL.
    """
    guards: dict[str, str] = {}
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint) and constraint.name:
            guards[constraint.name] = "unique constraint"
    for index in table.indexes:
        if index.unique and index.name:
            guards[index.name] = "unique index"
    return guards


def _live_uniqueness(inspector, table_name: str) -> set[str]:
    """Names of uniqueness objects the live schema reports for one table.

    A driver may surface the same guard as either a constraint or an index, so both
    are collected. Their presence also rules out the duplicate rows that the missing
    guard would have rejected, which is why no data scan is needed.
    """
    names = {item["name"] for item in inspector.get_unique_constraints(table_name)}
    names |= {item["name"] for item in inspector.get_indexes(table_name)}
    return {name for name in names if name}


def _schema_gaps(inspector, tables: set[str]) -> list[str]:
    """Describe why the live schema is not model-complete."""
    gaps: list[str] = []
    for name, table in Base.metadata.tables.items():
        if name not in tables:
            gaps.append(f"table {name!r} is missing")
            continue
        live = {column["name"]: column for column in inspector.get_columns(name)}
        for column in table.columns:
            if column.name not in live:
                gaps.append(f"column {name}.{column.name} is missing")
            elif bool(live[column.name]["nullable"]) != bool(column.nullable):
                gaps.append(f"column {name}.{column.name} nullability differs")
        present = _live_uniqueness(inspector, name)
        for guard, kind in _uniqueness_guards(table).items():
            if guard not in present:
                gaps.append(f"{kind} {guard!r} on {name} is missing")
    return gaps


def _adopt(connection, script_directory: ScriptDirectory) -> int:
    """Stamp the head revision onto a history-less schema, or refuse.

    Returns the process exit code: 0 when migrations can proceed, 1 when the
    schema is partial and needs a human decision.
    """
    head = script_directory.get_current_head()
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())

    if not tables or tables == {"alembic_version"}:
        print("[adopt] No application tables found; migrations will create the schema.")
        return 0

    if "alembic_version" in tables:
        recorded = connection.execute(text("SELECT version_num FROM alembic_version")).all()
        if recorded:
            print(f"[adopt] Schema is already under migration management: {recorded[0][0]}")
            return 0

    gaps = _schema_gaps(inspector, tables)
    if gaps:
        print("[adopt] Refusing to adopt an incomplete schema:", file=sys.stderr)
        for gap in gaps:
            print(f"[adopt]   - {gap}", file=sys.stderr)
        print(
            "[adopt] Migrate by hand (for example `alembic stamp <revision>` then "
            "`alembic upgrade head`) or start from an empty database.",
            file=sys.stderr,
        )
        return 1

    MigrationContext.configure(connection).stamp(script_directory, head)
    print(f"[adopt] History-less schema adopted at {head}.")
    return 0


async def main() -> int:
    """Adopt through the app's own engine, so the driver and URL match the migrations."""
    async with engine.begin() as connection:
        return await connection.run_sync(_adopt, _script_directory())


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
