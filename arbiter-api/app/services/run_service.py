from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pipeline import Pipeline, RunStatus
from app.models.pipeline_run import PipelineRun
from app.models.task_instance import TaskInstance
from app.schemas.pipeline import PipelineCreate, PipelineRunDetail, PipelineRunSummary
from app.schemas.run import RunPayload
from app.services.alert_service import process_run_event_sync
from app.services.pipeline_service import create_pipeline, upsert_dag_definition

logger = logging.getLogger(__name__)


async def ingest_run(session: AsyncSession, org_id, payload: RunPayload) -> PipelineRun:
    pipeline = await create_pipeline(
        session,
        org_id,
        PipelineCreate(name=payload.pipeline, source=payload.source, dag_id=payload.dag_id),
        dag_id=payload.dag_id,
    )

    # SELECT FOR UPDATE serializes concurrent upserts for the same (pipeline_id, run_id).
    # Without this lock, two simultaneous requests both read None and both INSERT,
    # producing duplicate rows (there was no UNIQUE constraint before 0002_unique_run_id).
    result = await session.execute(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == pipeline.id, PipelineRun.run_id == payload.run_id)
        .with_for_update()
    )
    run = result.scalar_one_or_none()
    if run is None:
        run = PipelineRun(
            pipeline_id=pipeline.id,
            run_id=payload.run_id,
            status=payload.status,
            started_at=payload.started_at,
            finished_at=payload.finished_at,
            duration_ms=payload.duration_ms,
            error_message=payload.error_message,
        )
    else:
        run.status = payload.status
        run.started_at = payload.started_at
        run.finished_at = payload.finished_at
        run.duration_ms = payload.duration_ms
        run.error_message = payload.error_message
    session.add(run)
    # Flush to get run.id without committing — tasks and dag_definition
    # are added below in the same transaction.
    await session.flush()

    # Delete-and-reinsert tasks within the same transaction as the run flush.
    # This is now atomic: if anything fails, the whole transaction rolls back.
    await session.execute(delete(TaskInstance).where(TaskInstance.run_id == run.id))
    for task_payload in payload.tasks:
        task = TaskInstance(
            run_id=run.id,
            task_id=task_payload.task_id,
            status=task_payload.status,
            started_at=task_payload.started_at,
            finished_at=task_payload.finished_at,
            duration_ms=task_payload.duration_ms,
            try_number=task_payload.try_number,
            log_url=task_payload.log_url,
            error_message=task_payload.error_message,
            input_params=task_payload.input_params,
        )
        session.add(task)

    if payload.nodes or payload.edges:
        # upsert_dag_definition no longer commits internally
        await upsert_dag_definition(session, pipeline, payload.nodes, payload.edges)

    # process_run_event_sync updates pipeline.last_run_status and creates alerts —
    # all still in the same open transaction.
    await process_run_event_sync(session, run)

    # Single commit covering: run, tasks, dag_definition, pipeline metadata, alert.
    await session.commit()
    await session.refresh(run)
    logger.info("run_ingested", extra={"run_id": str(run.id), "pipeline_id": str(pipeline.id)})
    return run


async def list_runs(
    session: AsyncSession,
    org_id,
    *,
    run_status: RunStatus | None = None,
    pipeline_id: UUID | None = None,
    started_from: datetime | None = None,
    started_to: datetime | None = None,
    query: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[PipelineRunDetail], int]:
    """Page through every run of the organisation, newest started first.

    Only runs of the caller's organisation are visible, so the pipeline join is
    part of every query and each filter also narrows the counted total.
    """
    conditions = [Pipeline.org_id == org_id]
    if run_status is not None:
        conditions.append(PipelineRun.status == run_status)
    if pipeline_id is not None:
        conditions.append(PipelineRun.pipeline_id == pipeline_id)
    if started_from is not None:
        conditions.append(PipelineRun.started_at >= started_from)
    if started_to is not None:
        conditions.append(PipelineRun.started_at <= started_to)
    if query:
        # lower() + like() instead of ilike keeps this portable across SQLite and PostgreSQL.
        pattern = f"%{query.lower()}%"
        conditions.append(
            or_(
                func.lower(PipelineRun.run_id).like(pattern),
                func.lower(PipelineRun.error_message).like(pattern),
            )
        )

    count_statement = (
        select(func.count())
        .select_from(PipelineRun)
        .join(Pipeline, Pipeline.id == PipelineRun.pipeline_id)
        .where(*conditions)
    )
    total_result = await session.execute(count_statement)
    result = await session.execute(
        select(PipelineRun, Pipeline.name)
        .join(Pipeline, Pipeline.id == PipelineRun.pipeline_id)
        .where(*conditions)
        .order_by(PipelineRun.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [
        PipelineRunDetail(
            **PipelineRunSummary.model_validate(run).model_dump(),
            pipeline_id=run.pipeline_id,
            pipeline_name=pipeline_name,
        )
        for run, pipeline_name in result.all()
    ]
    return items, total_result.scalar_one()


async def get_run(session: AsyncSession, run_id, org_id) -> PipelineRun | None:
    try:
        run_uuid = UUID(str(run_id))
    except ValueError:
        return None  # malformed UUID → caller raises 404, no 500
    result = await session.execute(
        select(PipelineRun)
        .join(Pipeline)
        .where(PipelineRun.id == run_uuid, Pipeline.org_id == org_id)
        .options(selectinload(PipelineRun.task_instances))
    )
    return result.scalar_one_or_none()


async def list_tasks(session: AsyncSession, run_id, org_id):
    run = await get_run(session, run_id, org_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return list(run.task_instances)