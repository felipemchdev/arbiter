"""add unique constraint on pipeline_runs(pipeline_id, run_id)

Revision ID: 0002_unique_run_id
Revises: 0001_initial
Create Date: 2026-06-04
"""

from alembic import op

revision = "0002_unique_run_id"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        # SQLite does not support DISTINCT ON, so we use a subquery with GROUP BY
        # to identify the most-recently created row per (pipeline_id, run_id) pair.
        op.execute(
            """
            DELETE FROM pipeline_runs
            WHERE id NOT IN (
                SELECT id FROM pipeline_runs
                WHERE (pipeline_id, run_id, created_at) IN (
                    SELECT pipeline_id, run_id, MAX(created_at)
                    FROM pipeline_runs
                    GROUP BY pipeline_id, run_id
                )
            )
            """
        )
        # SQLite cannot add unique constraints via ALTER TABLE in the normal Alembic
        # path; batch_alter_table() recreates the table under the hood, which is the
        # only way to enforce a new uniqueness constraint on an existing SQLite table.
        with op.batch_alter_table("pipeline_runs") as batch_op:
            batch_op.create_unique_constraint(
                "uq_pipeline_runs_pipeline_run_id",
                ["pipeline_id", "run_id"],
            )
    else:
        # PostgreSQL supports DISTINCT ON for an efficient single-pass duplicate
        # removal that keeps the most-recently created row per (pipeline_id, run_id).
        op.execute(
            """
            DELETE FROM pipeline_runs
            WHERE id NOT IN (
                SELECT DISTINCT ON (pipeline_id, run_id) id
                FROM pipeline_runs
                ORDER BY pipeline_id, run_id, created_at DESC
            )
            """
        )
        op.create_unique_constraint(
            "uq_pipeline_runs_pipeline_run_id",
            "pipeline_runs",
            ["pipeline_id", "run_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        # SQLite requires batch_alter_table() to drop constraints as well.
        with op.batch_alter_table("pipeline_runs") as batch_op:
            batch_op.drop_constraint(
                "uq_pipeline_runs_pipeline_run_id", type_="unique"
            )
    else:
        op.drop_constraint(
            "uq_pipeline_runs_pipeline_run_id", "pipeline_runs", type_="unique"
        )
