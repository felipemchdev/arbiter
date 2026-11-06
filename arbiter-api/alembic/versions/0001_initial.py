"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _enum(dialect_name: str, name: str, values: tuple[str, ...]):
    """Build one enum for the target dialect.

    ``op.create_table`` fires the type's ``before_create`` event with
    ``checkfirst=False``, so a native PostgreSQL enum emits a second
    ``CREATE TYPE`` next to the explicit ``create()`` calls below.
    ``create_type=False`` keeps those calls as the only type DDL.
    """
    if dialect_name == "postgresql":
        return postgresql.ENUM(*values, name=name, create_type=False)
    return sa.Enum(*values, name=name)


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    source_enum = _enum(dialect_name, "pipelinesource", ("airflow", "azure_function", "sdk"))
    run_status_enum = _enum(dialect_name, "runstatus", ("running", "success", "failed", "skipped"))
    task_status_enum = _enum(
        dialect_name, "taskstatus", ("running", "success", "failed", "skipped", "upstream_failed")
    )
    alert_type_enum = _enum(dialect_name, "alerttype", ("failure", "duration_exceeded", "no_run"))

    source_enum.create(bind, checkfirst=True)
    run_status_enum.create(bind, checkfirst=True)
    task_status_enum.create(bind, checkfirst=True)
    alert_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, index=True),
        sa.Column("api_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False, index=True),
        sa.Column("source", source_enum, nullable=False),
        sa.Column("dag_id", sa.String(length=255), nullable=True),
        sa.Column("last_run_status", run_status_enum, nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("pipeline_id", sa.Uuid(), sa.ForeignKey("pipelines.id"), nullable=False, index=True),
        sa.Column("run_id", sa.String(length=255), nullable=False, index=True),
        sa.Column("status", run_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "task_instances",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("pipeline_runs.id"), nullable=False, index=True),
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("status", task_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("try_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("log_url", sa.String(length=1000), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_table(
        "dag_definitions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("pipeline_id", sa.Uuid(), sa.ForeignKey("pipelines.id"), nullable=False, unique=True),
        sa.Column("nodes", sa.JSON(), nullable=False),
        sa.Column("edges", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("pipeline_id", sa.Uuid(), sa.ForeignKey("pipelines.id"), nullable=False, index=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("pipeline_runs.id"), nullable=True),
        sa.Column("type", alert_type_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("dag_definitions")
    op.drop_table("task_instances")
    op.drop_table("pipeline_runs")
    op.drop_table("pipelines")
    op.drop_table("organizations")