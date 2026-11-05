"""add slow_threshold_ms to pipelines

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("pipelines") as batch_op:
        batch_op.add_column(sa.Column("slow_threshold_ms", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("pipelines") as batch_op:
        batch_op.drop_column("slow_threshold_ms")
