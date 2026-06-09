"""migrate Organization.api_key to ApiKey table, then drop the column

Revision ID: 0007_migrate_org_api_key_to_table
Revises: 0006_api_keys_refresh_tokens
Create Date: 2026-06-08
"""

import uuid
from datetime import UTC, datetime
from secrets import token_urlsafe

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_migrate_org_api_key_to_table"
down_revision = "0006_api_keys_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "sqlite":
        rows = conn.execute(sa.text("SELECT id, name, api_key FROM organizations")).fetchall()
        now = datetime.now(UTC).isoformat()
        for row in rows:
            org_id = str(row[0])
            org_name = row[1]
            old_hash = row[2]
            migrated_name = f"{org_name} (migrated)"
            prefix = "arb_migrated_"
            new_id = str(uuid.uuid4())
            conn.execute(
                sa.text(
                    "INSERT INTO api_keys (id, org_id, name, environment, prefix, hashed_key, scopes, created_at, revoked) "
                    "VALUES (:id, :org_id, :name, :environment, :prefix, :hashed_key, :scopes, :created_at, :revoked)"
                ),
                {
                    "id": new_id,
                    "org_id": org_id,
                    "name": migrated_name,
                    "environment": "production",
                    "prefix": prefix,
                    "hashed_key": old_hash,
                    "scopes": "collector:write",
                    "created_at": now,
                    "revoked": False,
                },
            )
    else:
        rows = conn.execute(sa.text("SELECT id, name, api_key FROM organizations")).fetchall()
        now = datetime.now(UTC)
        for row in rows:
            org_id = row[0]
            org_name = row[1]
            old_hash = row[2]
            migrated_name = f"{org_name} (migrated)"
            new_id = uuid.uuid4()
            conn.execute(
                sa.text(
                    "INSERT INTO api_keys (id, org_id, name, environment, prefix, hashed_key, scopes, created_at, revoked) "
                    "VALUES (:id, :org_id, :name, :environment, :prefix, :hashed_key, :scopes, :created_at, :revoked)"
                ),
                {
                    "id": new_id,
                    "org_id": org_id,
                    "name": migrated_name,
                    "environment": "production",
                    "prefix": "arb_migrated_",
                    "hashed_key": old_hash,
                    "scopes": "collector:write",
                    "created_at": now,
                    "revoked": False,
                },
            )

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_index("ix_organizations_api_key")
        batch_op.drop_column("api_key")


def downgrade():
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(sa.Column("api_key", sa.String(length=255), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT ak.org_id, ak.hashed_key FROM api_keys ak "
            "WHERE ak.name LIKE '%(migrated)' AND ak.revoked = false"
        )
    ).fetchall()

    for row in rows:
        org_id = row[0]
        hashed_key = row[1]
        conn.execute(
            sa.text("UPDATE organizations SET api_key = :hashed_key WHERE id = :org_id"),
            {"hashed_key": hashed_key, "org_id": org_id},
        )

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.alter_column("api_key", nullable=False)
        batch_op.create_index("ix_organizations_api_key", ["api_key"], unique=True)
