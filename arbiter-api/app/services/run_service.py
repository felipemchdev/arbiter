from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pipeline import Pipeline, PipelineSource, RunStatus
from app.models.pipeline_run import PipelineRun
from app.models.task_instance import TaskInstance, TaskStatus
from app.schemas.pipeline import PipelineCreate
from app.schemas.run import RunPayload
from app.services.alert_service import process_run_event_sync
from app.services.pipeline_service import create_pipeline, upsert_dag_definition

logger = logging.getLogger(__name__)


async def ingest_run(session: AsyncSession, org_id, payload: RunPayload) -> PipelineRun:
    pipeline = await create_pipeline(
        session,
        org_id,
        PipelineCreate(name=payload.pipeline, source=PipelineSource(payload.source), dag_id=payload.dag_id),
        dag_id=payload.dag_id,
    )

    result = await session.execute(
        select(PipelineRun).where(PipelineRun.pipeline_id == pipeline.id, PipelineRun.run_id == payload.run_id)
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
    await session.commit()
    await session.refresh(run)

    await session.execute(delete(TaskInstance).where(TaskInstance.run_id == run.id))
    for task_payload in payload.tasks:
        task = TaskInstance(
            run_id=run.id,
            task_id=task_payload.task_id,
            status=TaskStatus(task_payload.status),
            started_at=task_payload.started_at,
            finished_at=task_payload.finished_at,
            duration_ms=task_payload.duration_ms,
            try_number=task_payload.try_number,
            log_url=task_payload.log_url,
            error_message=task_payload.error_message,
        )
        session.add(task)

    if payload.nodes or payload.edges:
        await upsert_dag_definition(session, pipeline, payload.nodes, payload.edges)

    await session.commit()
    await session.refresh(run)

    await process_run_event_sync(session, run)
    logger.info("run_ingested", extra={"run_id": str(run.id), "pipeline_id": str(pipeline.id)})
    return run


async def get_run(session: AsyncSession, run_id, org_id) -> PipelineRun | None:
    run_uuid = UUID(str(run_id))
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