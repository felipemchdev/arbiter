"""create notification_channels table

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("signing_secret", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_channels_org_id", "notification_channels", ["org_id"])


def downgrade():
    op.drop_index("ix_notification_channels_org_id", table_name="notification_channels")
    op.drop_table("notification_channels")
