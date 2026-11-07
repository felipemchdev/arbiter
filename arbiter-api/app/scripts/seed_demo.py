"""Seed a generic demo pipeline so a fresh install has something to render.

Idempotent: keyed on ``dag_id`` for the pipeline and on a deterministic
``run_id`` per day, so re-running the seeder never collides with the
``pipeline_runs(pipeline_id, run_id)`` unique constraint.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import async_session_maker, init_models
from app.models.alert import Alert, AlertType
from app.models.dag_definition import DagDefinition
from app.models.organization import Organization
from app.models.pipeline import Pipeline, PipelineSource, RunStatus
from app.models.pipeline_run import PipelineRun
from app.models.task_instance import TaskInstance, TaskStatus

DAG_ID = "demo_nightly_sales_etl"
PIPELINE_NAME = "Nightly Sales ETL (demo)"
RUN_HOUR_UTC = 2
RUNS_TO_SEED = 7

TASKS = [
    {"task_id": "extract_sales", "label": "Extract sales", "duration_ms": 6400},
    {"task_id": "clean_sales", "label": "Clean sales", "duration_ms": 9800},
    {"task_id": "aggregate_daily", "label": "Aggregate daily", "duration_ms": 15200},
    {"task_id": "publish_report", "label": "Publish report", "duration_ms": 4300},
]

DAY_STATUSES = [
    RunStatus.running,
    RunStatus.failed,
    RunStatus.success,
    RunStatus.success,
    RunStatus.skipped,
    RunStatus.success,
    RunStatus.success,
]


def _run_id(day: datetime) -> str:
    """Deterministic Airflow-style run id, so re-running the seed is a no-op."""
    return f"scheduled__{day:%Y-%m-%dT%H:%M:%S}"


async def main() -> None:
    """Create or refresh the demo pipeline and its last seven daily runs."""
    await init_models()
    async with async_session_maker() as session:
        org = (await session.execute(select(Organization).limit(1))).scalar_one_or_none()
        if org is None:
            print("[seed:demo] No organization found - run seed_dev first, skipping.")
            return

        # Scoped to this org: dag_id is only unique per organisation, so an
        # unscoped lookup could attach demo runs to another org's pipeline.
        pipeline = (
            await session.execute(
                select(Pipeline).where(
                    Pipeline.dag_id == DAG_ID,
                    Pipeline.org_id == org.id,
                )
            )
        ).scalar_one_or_none()
        if pipeline is None:
            # Matching on dag_id alone would let a pipeline that already owns this
            # name but a different dag_id slip through, and the insert would put
            # two identically named rows in front of the dashboard.
            name_taken = (
                await session.execute(
                    select(Pipeline.id)
                    .where(Pipeline.org_id == org.id, Pipeline.name == PIPELINE_NAME)
                    .limit(1)
                )
            ).scalar_one_or_none()
            if name_taken is not None:
                print(f"[seed:demo] Name already used by another pipeline: {PIPELINE_NAME} - skipping.")
                return

            pipeline = Pipeline(
                id=uuid.uuid4(),
                org_id=org.id,
                name=PIPELINE_NAME,
                source=PipelineSource.airflow,
                dag_id=DAG_ID,
                # Above every seeded duration (36700 ms), so the demo shows a budget
                # without showing a false alert.
                slow_threshold_ms=45_000,
            )
            session.add(pipeline)
            await session.flush()
            nodes = [{"id": t["task_id"], "label": t["label"], "type": "task"} for t in TASKS]
            edges = [
                {"source": TASKS[i]["task_id"], "target": TASKS[i + 1]["task_id"]}
                for i in range(len(TASKS) - 1)
            ]
            session.add(DagDefinition(pipeline_id=pipeline.id, nodes=nodes, edges=edges))
            print(f"[seed:demo] Pipeline created: {DAG_ID}")

        today = datetime.now(UTC).replace(hour=RUN_HOUR_UTC, minute=0, second=0, microsecond=0)
        existing_runs = set(
            (
                await session.execute(
                    select(PipelineRun.run_id).where(PipelineRun.pipeline_id == pipeline.id)
                )
            ).scalars()
        )

        created = 0
        for offset in range(RUNS_TO_SEED):
            day = today - timedelta(days=offset)
            run_id = _run_id(day)
            if run_id in existing_runs:
                continue
            status = DAY_STATUSES[offset % len(DAY_STATUSES)]
            running = status is RunStatus.running
            duration_ms = sum(t["duration_ms"] for t in TASKS) + 250 * len(TASKS)
            run = PipelineRun(
                id=uuid.uuid4(),
                pipeline_id=pipeline.id,
                run_id=run_id,
                status=status,
                started_at=day,
                finished_at=None if running else day + timedelta(milliseconds=duration_ms),
                duration_ms=None if running else duration_ms,
                error_message="Task publish_report failed: target table not found"
                if status is RunStatus.failed
                else None,
            )
            session.add(run)
            await session.flush()

            cursor = day
            for task in TASKS:
                task_failed = status is RunStatus.failed and task is TASKS[-1]
                task_status = (
                    TaskStatus.running
                    if running
                    else TaskStatus.failed
                    if task_failed
                    else TaskStatus.skipped
                    if status is RunStatus.skipped
                    else TaskStatus.success
                )
                session.add(
                    TaskInstance(
                        id=uuid.uuid4(),
                        run_id=run.id,
                        task_id=task["task_id"],
                        status=task_status,
                        started_at=cursor,
                        finished_at=None
                        if running
                        else cursor + timedelta(milliseconds=task["duration_ms"]),
                        duration_ms=None if running else task["duration_ms"],
                        try_number=1,
                        error_message="Table 'sales_report' does not exist" if task_failed else None,
                    )
                )
                cursor += timedelta(milliseconds=task["duration_ms"] + 250)
            created += 1

        runs = (
            await session.execute(
                select(PipelineRun)
                .where(PipelineRun.pipeline_id == pipeline.id)
                .order_by(PipelineRun.started_at.desc())
            )
        ).scalars().all()
        if runs:
            pipeline.last_run_status = runs[0].status
            pipeline.last_run_at = runs[0].started_at

        alerted = set(
            (
                await session.execute(
                    select(Alert.run_id).where(
                        Alert.pipeline_id == pipeline.id, Alert.type == AlertType.failure
                    )
                )
            ).scalars()
        )
        for run in runs:
            if run.status is not RunStatus.failed or run.id in alerted:
                continue
            session.add(
                Alert(
                    id=uuid.uuid4(),
                    pipeline_id=pipeline.id,
                    run_id=run.id,
                    type=AlertType.failure,
                    message=f"{PIPELINE_NAME}: {run.error_message}",
                    resolved=False,
                )
            )

        await session.commit()
        print(f"[seed:demo] Done ({created} run(s) added).")


if __name__ == "__main__":
    asyncio.run(main())
