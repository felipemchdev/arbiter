from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect, text

import app.models  # noqa: F401
from app.core.database import Base
from app.scripts.adopt_baseline import _adopt, _schema_gaps, _script_directory


@pytest.fixture(scope="module")
def script_directory():
    """Load the migration scripts once; the tests only read them."""
    return _script_directory()


def test_adopts_schema_created_without_history(tmp_path, script_directory):
    """A create_all schema has no alembic_version row, so the head is stamped."""
    engine = create_engine(f"sqlite:///{tmp_path / 'history_less.db'}")
    Base.metadata.create_all(engine)

    with engine.connect() as connection:
        assert _adopt(connection, script_directory) == 0
        connection.commit()
        stamped = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()

    assert stamped == [script_directory.get_current_head()]


def test_refuses_partial_schema(tmp_path, script_directory):
    """A schema missing a model table must not be claimed as migrated."""
    engine = create_engine(f"sqlite:///{tmp_path / 'partial.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE alerts"))

    with engine.connect() as connection:
        assert _adopt(connection, script_directory) == 1
        assert "alembic_version" not in inspect(connection).get_table_names()


def test_refuses_schema_without_a_unique_index(tmp_path, script_directory):
    """Alembic 0003 protects active alerts from duplicates; stamping must not skip it."""
    engine = create_engine(f"sqlite:///{tmp_path / 'no_alert_index.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text('DROP INDEX "uq_active_alert"'))

    with engine.connect() as connection:
        gaps = _schema_gaps(inspect(connection), set(inspect(connection).get_table_names()))
        assert "unique index 'uq_active_alert' on alerts is missing" in gaps
        assert _adopt(connection, script_directory) == 1


def test_refuses_schema_without_a_unique_constraint(tmp_path, script_directory):
    """Alembic 0002 protects (pipeline_id, run_id); a schema without it is refused."""
    engine = create_engine(f"sqlite:///{tmp_path / 'no_run_guard.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE pipeline_runs RENAME TO pipeline_runs_guardless"))
        connection.execute(
            text(
                """
                CREATE TABLE pipeline_runs (
                    id CHAR(32) NOT NULL PRIMARY KEY,
                    pipeline_id CHAR(32) NOT NULL,
                    run_id VARCHAR(255) NOT NULL,
                    status VARCHAR(9) NOT NULL,
                    started_at DATETIME NOT NULL,
                    finished_at DATETIME,
                    duration_ms INTEGER,
                    error_message TEXT,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )

    with engine.connect() as connection:
        gaps = _schema_gaps(inspect(connection), set(inspect(connection).get_table_names()))
        assert "unique constraint 'uq_pipeline_runs_pipeline_run_id' on pipeline_runs is missing" in gaps
        assert _adopt(connection, script_directory) == 1


def test_ignores_missing_non_unique_index(tmp_path, script_directory):
    """A plain index only affects speed, so it never blocks adoption."""
    engine = create_engine(f"sqlite:///{tmp_path / 'slow_but_valid.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text('DROP INDEX "ix_alerts_pipeline_id"'))

    with engine.connect() as connection:
        assert _adopt(connection, script_directory) == 0


def _rebuilt_alert_index(tmp_path, db_name, index_ddl: str) -> list[str]:
    """Return the gaps of a create_all schema whose alert guard is index_ddl."""
    engine = create_engine(f"sqlite:///{tmp_path / db_name}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text('DROP INDEX "uq_active_alert"'))
        connection.execute(text(index_ddl))
    with engine.connect() as connection:
        return _schema_gaps(inspect(connection), set(inspect(connection).get_table_names()))


def test_refuses_a_plain_index_that_only_borrows_the_guard_name(tmp_path, script_directory):
    """A non-unique index named uq_active_alert still allows duplicate active alerts."""
    engine = create_engine(f"sqlite:///{tmp_path / 'borrowed_name.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text('DROP INDEX "uq_active_alert"'))
        connection.execute(
            text("CREATE INDEX uq_active_alert ON alerts (pipeline_id, type, run_id, message)")
        )

    with engine.connect() as connection:
        gaps = _schema_gaps(inspect(connection), set(inspect(connection).get_table_names()))
        assert "unique index 'uq_active_alert' on alerts is missing" in gaps
        assert _adopt(connection, script_directory) == 1


def test_refuses_a_guard_over_the_wrong_columns(tmp_path):
    """The guard must cover the columns revision 0003 declares, not a subset."""
    gaps = _rebuilt_alert_index(
        tmp_path, "wrong_columns.db", "CREATE UNIQUE INDEX uq_active_alert ON alerts (pipeline_id)"
    )
    assert "unique index 'uq_active_alert' on alerts covers a different column set" in gaps


def test_refuses_a_guard_without_its_partial_predicate(tmp_path):
    """A full unique index also blocks a new alert after the first one is resolved."""
    gaps = _rebuilt_alert_index(
        tmp_path,
        "not_partial.db",
        "CREATE UNIQUE INDEX uq_active_alert ON alerts (pipeline_id, type, run_id, message)",
    )
    assert "unique index 'uq_active_alert' on alerts is not a partial index" in gaps


def test_refuses_a_guard_with_the_wrong_predicate(tmp_path):
    """An index over resolved rows lets every live duplicate through."""
    gaps = _rebuilt_alert_index(
        tmp_path,
        "wrong_predicate.db",
        "CREATE UNIQUE INDEX uq_active_alert "
        "ON alerts (pipeline_id, type, run_id, message) WHERE resolved = 1",
    )
    assert "unique index 'uq_active_alert' on alerts has a different predicate" in gaps


def test_accepts_a_guard_written_with_other_spacing(tmp_path):
    """Spacing and grouping brackets are spelling, not a different rule."""
    gaps = _rebuilt_alert_index(
        tmp_path,
        "spaced_predicate.db",
        "CREATE UNIQUE INDEX uq_active_alert "
        "ON alerts (pipeline_id, type, run_id, message) WHERE (resolved = 0)",
    )
    assert gaps == []


def test_create_all_schema_carries_the_migration_guards():
    """The models mirror the revisions, so databases the seeders build are adoptable."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)

    run_guards = {c["name"] for c in inspector.get_unique_constraints("pipeline_runs")}
    alert_guards = {i["name"] for i in inspector.get_indexes("alerts") if i["unique"]}

    assert "uq_pipeline_runs_pipeline_run_id" in run_guards
    assert "uq_active_alert" in alert_guards


def test_leaves_managed_and_empty_databases_alone(tmp_path, script_directory):
    """Already-versioned and empty databases keep the normal migration behaviour."""
    managed = create_engine(f"sqlite:///{tmp_path / 'managed.db'}")
    Base.metadata.create_all(managed)
    with managed.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(255))"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('0001_initial')"))

    with managed.connect() as connection:
        assert _adopt(connection, script_directory) == 0
        rows = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    assert rows == ["0001_initial"]

    empty = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    with empty.connect() as connection:
        assert _adopt(connection, script_directory) == 0
        assert inspect(connection).get_table_names() == []
