"""add prefix index on api_keys for O(1) lookup

Revision ID: 0008
Revises: 0007_migrate_org_api_key_to_table
Create Date: 2026-06-09
"""

from alembic import op

revision = "0008"
down_revision = "0007_migrate_org_api_key_to_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_api_keys_prefix", "api_keys", ["prefix"])


def downgrade():
    op.drop_index("ix_api_keys_prefix")
