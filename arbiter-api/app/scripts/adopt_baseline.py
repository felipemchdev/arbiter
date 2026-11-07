"""Adopt a schema that exists without Alembic history so migrations can run.

The seeders build tables with ``Base.metadata.create_all``, which never writes an
``alembic_version`` row. On the next start ``alembic upgrade head`` replays the
initial migration against tables that already exist, the process exits non-zero,
and the container restart policy repeats that failure forever.

The head revision is stamped only when the live schema is compatible with the
models: every model table, every model column with a type that can hold what the
model writes, every foreign key the models declare, the uniqueness guards the
application relies on, and no row that already breaks them. A guard is matched by
name, by its columns and by its partial predicate, so a plain index that only
borrows the name of a guard does not pass, and a partial index does not stand in
for the full uniqueness a revision declares. A schema that fails is refused
instead: stamping it would tell Alembic the database is current while a
protection that later revisions add - the unique run key, the active-alert index
or the run key foreign key - is still missing.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import ForeignKeyConstraint, and_, func, inspect, or_, select, text
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import NullType

import app.models  # noqa: F401
from app.core.database import Base, engine

API_ROOT = Path(__file__).resolve().parents[2]

# The get_indexes key that reports a partial index predicate, by driver.
_PREDICATE_KEYS = {"postgresql": "postgresql_where", "sqlite": "sqlite_where"}

# A server re-prints a stored predicate with the casts its parser inferred.
_INFERRED_CAST = re.compile(
    r"::(?:character varying|double precision|timestamp with time zone|[a-z_][a-z0-9_]*)"
    r"(?:\[\])?"
)
# A quoted string is a value, not syntax, so it survives the comparison untouched.
_SQL_LITERAL = re.compile(r"'(?:[^']|'')*'")
_LITERAL_SLOT = re.compile("\x00([0-9]+)\x00")
_PREDICATE_NOISE = re.compile(r'[\s()"]+')
_TYPE_ARGS = re.compile(r"\([^)]*\)")
_TYPE_NAMES = (
    ("timestamp with time zone", "timestamp"),
    ("time with time zone", "time"),
    ("character varying", "varchar"),
    ("double precision", "double precision"),
)
# SQLite keeps only the five affinities its rules derive from a declared type name.
_SQLITE_AFFINITIES = (
    ("INT", "integer"),
    (("CHAR", "CLOB", "TEXT"), "text"),
    ("BLOB", "blob"),
    (("REAL", "FLOA", "DOUB"), "real"),
)


def _normalized_predicate(clause) -> str | None:
    """Reduce a WHERE clause to the text both sides of the comparison can agree on.

    A driver re-prints a predicate it stored: PostgreSQL adds grouping brackets
    and the casts its parser inferred. Spacing, brackets, inferred casts and
    quoted identifiers are removed and the rest is lower case, so an equivalent
    guard still matches. String literals are set aside first and put back
    unchanged, because the value a guard selects on is case sensitive.
    """
    if clause is None:
        return None
    literals: list[str] = []

    def _reserve(match: re.Match) -> str:
        literals.append(match.group(0))
        return f"\x00{len(literals) - 1}\x00"

    skeleton = _SQL_LITERAL.sub(_reserve, str(clause))
    skeleton = _PREDICATE_NOISE.sub("", _INFERRED_CAST.sub("", skeleton))
    return _LITERAL_SLOT.sub(lambda slot: literals[int(slot.group(1))], skeleton.lower())


def _rendered_type(type_instance, dialect) -> str:
    """The spelling of one column type in the dialect the live schema speaks."""
    rendered = str(type_instance.compile(dialect=dialect)).lower()
    for long_name, short_name in _TYPE_NAMES:
        rendered = rendered.replace(long_name, short_name)
    return " ".join(_TYPE_ARGS.sub("", rendered).split())


def _sqlite_affinity(rendered: str) -> str:
    """The affinity SQLite gives a column whose declared type reads as rendered."""
    name = rendered.upper()
    for token, affinity in _SQLITE_AFFINITIES:
        needles = (token,) if isinstance(token, str) else token
        if any(needle in name for needle in needles):
            return affinity
    return "numeric"


def _column_type_gap(column, live_column, dialect) -> str | None:
    """Why a live column cannot hold what the model writes to it, if it cannot.

    PostgreSQL and SQLite report the type they store, not the object the model
    declared, so the two sides are compared as the dialect spells them. SQLite
    reduces every declared type to one of its affinities, because it keeps
    nothing else. A width is compared only when both sides report one.
    """
    model_type = _rendered_type(column.type, dialect)
    live_type = _rendered_type(live_column["type"], dialect)
    if dialect.name == "sqlite":
        if _sqlite_affinity(model_type) != _sqlite_affinity(live_type):
            return f"column {column.table.name}.{column.name} holds {live_type}, not {model_type}"
    elif model_type != live_type:
        return f"column {column.table.name}.{column.name} holds {live_type}, not {model_type}"
    model_width = getattr(column.type, "length", None)
    live_width = getattr(live_column["type"], "length", None)
    if model_width is not None and live_width is not None and live_width < model_width:
        return f"column {column.table.name}.{column.name} is {live_width} wide, not {model_width}"
    return None


def _required_references(table) -> dict[str, dict]:
    """The foreign keys one table must carry, by the columns that hold them."""
    wanted: dict[str, dict] = {}
    for constraint in table.constraints:
        if isinstance(constraint, ForeignKeyConstraint):
            local = ",".join(sorted(column.name for column in constraint.columns))
            wanted[local] = {
                "table": constraint.elements[0].column.table.name,
                "columns": frozenset(element.column.name for element in constraint.elements),
            }
    return wanted


def _live_references(inspector, table_name: str) -> dict[str, dict]:
    """The foreign keys the live schema reports for one table, by their columns."""
    found: dict[str, dict] = {}
    for item in inspector.get_foreign_keys(table_name):
        local = ",".join(sorted(item.get("constrained_columns") or ()))
        found[local] = {
            "table": item.get("referred_table"),
            "columns": frozenset(item.get("referred_columns") or ()),
        }
    return found


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
    human decision.
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
    """Describe why the live schema is not compatible with the models."""
    gaps: list[str] = []
    driver = inspector.dialect
    dialect = driver.name
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
            elif isinstance(live[column.name]["type"], NullType):
                gaps.append(f"column {name}.{column.name} has a type the driver cannot read")
            else:
                type_gap = _column_type_gap(column, live[column.name], driver)
                if type_gap:
                    gaps.append(type_gap)
        references = _live_references(inspector, name)
        for local, want in _required_references(table).items():
            got = references.get(local)
            if got is None:
                gaps.append(f"foreign key on {name} ({local}) is missing")
            elif got["table"] != want["table"]:
                gaps.append(f"foreign key on {name} ({local}) points at {got['table']}, not {want['table']}")
            elif got["columns"] and got["columns"] != want["columns"]:
                gaps.append(f"foreign key on {name} ({local}) points at different columns")
        present = _live_guards(inspector, name)
        for guard, want in _uniqueness_guards(table, dialect).items():
            found = present.get(guard)
            if found is None:
                gaps.append(f"{want['kind']} {guard!r} on {name} is missing")
            elif found["columns"] != want["columns"]:
                gaps.append(f"{want['kind']} {guard!r} on {name} covers a different column set")
            elif want["partial"] and found["partial"] is False:
                gaps.append(f"{want['kind']} {guard!r} on {name} is not a partial index")
            elif want["partial"] is False and found["partial"] is True:
                gaps.append(f"{want['kind']} {guard!r} on {name} is partial, and must not be")
            elif want["partial"] and found["predicate"] != want["predicate"]:
                gaps.append(f"{want['kind']} {guard!r} on {name} has a different predicate")
    return gaps


def _row_gaps(connection) -> list[str]:
    """Report rows that already break a reference the head schema declares.

    A schema built by ``create_all`` can hold orphans when the driver enforces
    foreign keys only when told to, which SQLite does by default. Stamping such
    a database would leave the orphans behind as if they were allowed.
    """
    gaps: list[str] = []
    for name, table in Base.metadata.tables.items():
        for constraint in table.constraints:
            if not isinstance(constraint, ForeignKeyConstraint):
                continue
            pairs = [(element.parent, element.column) for element in constraint.elements]
            local, remote = pairs[0]
            parent = remote.table
            statement = (
                select(func.count())
                .select_from(table)
                .outerjoin(parent, and_(*[child == ref for child, ref in pairs]))
                .where(
                    or_(*[child.is_not(None) for child, _ in pairs]),
                    parent.c[remote.name].is_(None),
                )
            )
            orphans = connection.execute(statement).scalar_one()
            if orphans:
                gaps.append(f"{orphans} row(s) of {name} reference a missing row of {parent.name}")
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

    dialect = inspector.dialect.name
    if dialect not in _PREDICATE_KEYS:
        print(
            f"[adopt] Refusing to adopt: the {dialect} driver is not compared against the models.",
            file=sys.stderr,
        )
        return 1

    gaps = _schema_gaps(inspector, tables)
    if not gaps:
        gaps = _row_gaps(connection)
    if gaps:
        print("[adopt] Refusing to adopt an incompatible schema:", file=sys.stderr)
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
