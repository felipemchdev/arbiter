"""Adopt a schema that exists without Alembic history so migrations can run.

The seeders build tables with ``Base.metadata.create_all``, which never writes an
``alembic_version`` row. On the next start ``alembic upgrade head`` replays the
initial migration against tables that already exist, the process exits non-zero,
and the container restart policy repeats that failure forever.

The head revision is stamped only when the live schema already holds every model
table, every model column and the uniqueness objects the application relies on.
A guard is matched by name, by its columns and by its partial predicate, so a
plain index that only borrows the name of a guard does not pass. A partial schema
is refused instead: stamping it would tell Alembic the database is
current while a protection that later revisions add - the unique run key or the
active-alert index - is still missing.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.schema import UniqueConstraint

import app.models  # noqa: F401
from app.core.database import Base, engine

API_ROOT = Path(__file__).resolve().parents[2]

# The get_indexes key that reports a partial index predicate, by driver.
_PREDICATE_KEYS = {"postgresql": "postgresql_where", "sqlite": "sqlite_where"}


def _normalized_predicate(clause) -> str | None:
    """Reduce a WHERE clause to the text both sides of the comparison can agree on.

    A driver may report the predicate with parentheses the model never wrote, and
    both drivers allow any spacing. Only whitespace and grouping brackets are
    removed; the operator spellings stay, so an index built for the wrong rows
    reads as a different predicate rather than as an equivalent one.
    """
    if clause is None:
        return None
    return re.sub(r"[\s()]+", "", str(clause)).lower()


def _script_directory() -> ScriptDirectory:
    """Load the migration scripts by absolute path, so the cwd does not matter."""
    config = Config(str(API_ROOT / "alembic.ini"))
    # alembic.ini predates this option; without it Alembic warns on every boot.
    config.set_main_option("path_separator", "os")
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    return ScriptDirectory.from_config(config)


def _uniqueness_guards(table, dialect: str) -> dict[str, dict]:
    """Return the named uniqueness objects a table must carry, in comparable form.

    Only objects that stop duplicate rows are required. Plain ``ix_*`` indexes are
    performance-only, and a missing one is repaired by ``CREATE INDEX``, not by a
    human decision. Column types stay unchecked: the driver returns dialect objects
    that do not compare reliably between SQLite and PostgreSQL.
    """
    reports_predicate = dialect in _PREDICATE_KEYS
    guards: dict[str, dict] = {}
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint) and constraint.name:
            guards[constraint.name] = {
                "kind": "unique constraint",
                "columns": frozenset(column.name for column in constraint.columns),
                "partial": False,
                "predicate": None,
            }
    for index in table.indexes:
        if not index.unique or not index.name:
            continue
        options = index.dialect_options.get(dialect) or {}
        where = options.get("where")
        guards[index.name] = {
            "kind": "unique index",
            "columns": frozenset(column.name for column in index.columns),
            # None means "not compared", never "must be absent". A predicate is a
            # clause object, so it is tested with `is not None`, never with truthness.
            "partial": (where is not None) if reports_predicate else None,
            "predicate": _normalized_predicate(where) if reports_predicate else None,
        }
    return guards


def _live_guards(inspector, table_name: str) -> dict[str, dict]:
    """Return the uniqueness objects the live schema reports for one table, by name.

    A non-unique index is never a guard: a plain index can carry the name of a
    unique object and still allow the duplicate rows the application forbids. A
    driver may surface the same guard as a constraint or as an index, so both are
    collected. Their columns are compared as a set and their predicates as
    normalized text, but only where the driver reports a predicate at all.
    """
    predicate_key = _PREDICATE_KEYS.get(inspector.dialect.name)
    guards: dict[str, dict] = {}
    for item in inspector.get_unique_constraints(table_name):
        if item.get("name"):
            guards[item["name"]] = {
                "kind": "unique constraint",
                "columns": frozenset(item.get("column_names") or ()),
                "partial": False,
                "predicate": None,
            }
    for item in inspector.get_indexes(table_name):
        if not item.get("name") or not item.get("unique"):
            continue
        where = item.get("dialect_options", {}).get(predicate_key) if predicate_key else None
        guards.setdefault(
            item["name"],
            {
                "kind": "unique index",
                # An expression index reports no column names, so it never matches.
                "columns": frozenset(item.get("column_names") or ()),
                "partial": (where is not None) if predicate_key else None,
                "predicate": _normalized_predicate(where) if predicate_key else None,
            },
        )
    return guards


def _schema_gaps(inspector, tables: set[str]) -> list[str]:
    """Describe why the live schema is not model-complete."""
    gaps: list[str] = []
    dialect = inspector.dialect.name
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
        present = _live_guards(inspector, name)
        for guard, want in _uniqueness_guards(table, dialect).items():
            found = present.get(guard)
            if found is None:
                gaps.append(f"{want['kind']} {guard!r} on {name} is missing")
            elif found["columns"] != want["columns"]:
                gaps.append(f"{want['kind']} {guard!r} on {name} covers a different column set")
            elif want["partial"] and found["partial"] is False:
                gaps.append(f"{want['kind']} {guard!r} on {name} is not a partial index")
            elif want["partial"] and found["predicate"] != want["predicate"]:
                gaps.append(f"{want['kind']} {guard!r} on {name} has a different predicate")
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
