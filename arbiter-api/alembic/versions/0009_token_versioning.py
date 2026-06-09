"""add token_version to users and refresh_tokens

Revision ID: 0009
Revises: 0008_api_keys_prefix_index
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008_api_keys_prefix_index"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    with op.batch_alter_table("refresh_tokens") as batch_op:
        batch_op.drop_column("token_version")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("token_version")
