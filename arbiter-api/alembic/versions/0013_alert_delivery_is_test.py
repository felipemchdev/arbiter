"""add is_test to alert_deliveries

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-06

Revision 0012 created alert_deliveries without the is_test column that
AlertDelivery maps, so every delivery insert on a migrated database failed.
Rows stored before this revision were all queued deliveries, which is_test
records as false.
"""

from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "alert_deliveries",
        sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    with op.batch_alter_table("alert_deliveries") as batch_op:
        batch_op.drop_column("is_test")
