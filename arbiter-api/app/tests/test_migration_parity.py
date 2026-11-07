from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

import app.models  # noqa: F401
from app.core.database import Base

API_ROOT = Path(__file__).resolve().parents[2]


def _migrated_engine(tmp_path: Path):
    db_path = tmp_path / "migrated.db"
    env = dict(os.environ, DATABASE_URL=f"sqlite+aiosqlite:///{db_path}")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    return create_engine(f"sqlite:///{db_path}")


def test_migrations_create_every_model_column(tmp_path):
    """A schema built by alembic must accept every mapped column the models write."""
    engine = _migrated_engine(tmp_path)
    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())

    problems = []
    for table in Base.metadata.sorted_tables:
        if table.name not in live_tables:
            problems.append(f"{table.name} is not created by any revision")
            continue
        live_columns = {column["name"] for column in inspector.get_columns(table.name)}
        missing = sorted(column.name for column in table.columns if column.name not in live_columns)
        if missing:
            problems.append(f"{table.name} is missing columns {missing}")

    assert not problems, "; ".join(problems)
