"""create alert_deliveries table

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def _enum(dialect_name: str, name: str, values: tuple[str, ...]):
    """Build one enum for the target dialect.

    The explicit ``create()`` call below is the only type DDL, so PostgreSQL does
    not receive a second ``CREATE TYPE`` from ``op.create_table``.
    """
    if dialect_name == "postgresql":
        return postgresql.ENUM(*values, name=name, create_type=False)
    return sa.Enum(*values, name=name)


def upgrade():
    bind = op.get_bind()
    status_enum = _enum(bind.dialect.name, "altdeliverystatus", ("pending", "delivered", "failed"))
    if bind.dialect.name == "postgresql":
        status_enum.create(bind, checkfirst=True)

    op.create_table(
        "alert_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("alert_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.ForeignKeyConstraint(["channel_id"], ["notification_channels.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alert_id", "channel_id", name="uq_alert_delivery_channel"),
    )
    op.create_index("ix_alert_deliveries_alert_id", "alert_deliveries", ["alert_id"])
    op.create_index("ix_alert_deliveries_channel_id", "alert_deliveries", ["channel_id"])
    op.create_index(
        "ix_alert_deliveries_status_next_attempt",
        "alert_deliveries",
        ["status", "next_attempt_at"],
    )


def downgrade():
    bind = op.get_bind()
    op.drop_index("ix_alert_deliveries_status_next_attempt", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_channel_id", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_alert_id", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
    if bind.dialect.name == "postgresql":
        postgresql.ENUM(name="altdeliverystatus").drop(bind, checkfirst=True)
