"""one open no_run alert per pipeline

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-06

uq_active_alert compares run_id, and a no_run alert has no run, so NULL made every
open no_run alert distinct and the stale check queued one more alert on every tick.
This revision keeps the oldest open no_run alert per pipeline and blocks the rest at
the database level.
"""

from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

_DUPLICATES = """
SELECT dup.id FROM alerts dup
WHERE dup.type = 'no_run' AND dup.resolved = false
  AND EXISTS (
    SELECT 1 FROM alerts keep
    WHERE keep.type = 'no_run' AND keep.resolved = false
      AND keep.pipeline_id = dup.pipeline_id
      AND (keep.created_at < dup.created_at
           OR (keep.created_at = dup.created_at AND keep.id < dup.id))
  )
"""


def upgrade():
    op.execute(sa.text("DELETE FROM alert_deliveries WHERE alert_id IN (" + _DUPLICATES + ")"))
    op.execute(sa.text("DELETE FROM alerts WHERE id IN (" + _DUPLICATES + ")"))
    op.create_index(
        "uq_open_no_run_alert",
        "alerts",
        ["pipeline_id"],
        unique=True,
        postgresql_where=sa.text("resolved = false AND type = 'no_run'"),
        sqlite_where=sa.text("resolved = 0 AND type = 'no_run'"),
    )


def downgrade():
    op.drop_index("uq_open_no_run_alert", table_name="alerts")
