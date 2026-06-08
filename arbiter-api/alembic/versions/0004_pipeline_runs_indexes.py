"""add performance indexes on pipeline_runs

Revision ID: 0004_pipeline_runs_indexes
Revises: b9c29e959ccb
Create Date: 2026-06-07 04:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_pipeline_runs_indexes"
down_revision: Union[str, None] = "b9c29e959ccb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index(
        "ix_pipeline_runs_pipeline_id_status",
        "pipeline_runs",
        ["pipeline_id", "status"],
    )

def downgrade():
    op.drop_index("ix_pipeline_runs_pipeline_id_status")
