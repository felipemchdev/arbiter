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
    # Remove duplicates that may already exist before adding the constraint.
    # Keep the most-recently created row per (pipeline_id, run_id) pair.
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
    op.drop_constraint("uq_pipeline_runs_pipeline_run_id", "pipeline_runs", type_="unique")
