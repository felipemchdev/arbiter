"""partial unique index for active alerts

Revision ID: 0003_unique_active_alert
Revises: 0002_unique_run_id
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_unique_active_alert"
down_revision = "0002_unique_run_id"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("uq_active_alert", "alerts", ["pipeline_id", "type", "run_id", "message"], unique=True, postgresql_where=sa.text("resolved = false"))


def downgrade():
    op.drop_index("uq_active_alert", table_name="alerts")
