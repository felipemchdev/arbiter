from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect, text

import app.models  # noqa: F401 - registers every table on Base.metadata
from app.core.database import Base
from app.scripts.adopt_baseline import _adopt, _script_directory


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
