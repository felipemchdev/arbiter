from alembic import op
import sqlalchemy as sa

revision = "0005_task_instance_payload"
down_revision = "0004_pipeline_runs_indexes"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("task_instances") as batch_op:
        batch_op.add_column(
            sa.Column("log_output", sa.Text(), nullable=True)
        )

        batch_op.add_column(
            sa.Column("input_params", sa.JSON(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("task_instances") as batch_op:
        batch_op.drop_column("input_params")
        batch_op.drop_column("log_output")