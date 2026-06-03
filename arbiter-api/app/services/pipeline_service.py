from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dag_definition import DagDefinition
from app.models.pipeline import Pipeline, PipelineSource
from app.schemas.pipeline import PipelineCreate
from app.services.alert_service import process_run_event_sync

logger = logging.getLogger(__name__)


async def list_pipelines(session: AsyncSession, org_id, limit: int = 50, offset: int = 0):
    result = await session.execute(
        select(Pipeline).where(Pipeline.org_id == org_id).order_by(Pipeline.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def create_pipeline(session: AsyncSession, org_id, payload: PipelineCreate, dag_id: str | None = None) -> Pipeline:
    result = await session.execute(
        select(Pipeline).where(Pipeline.org_id == org_id, Pipeline.name == payload.name)
    )
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        pipeline = Pipeline(org_id=org_id, name=payload.name, source=payload.source, dag_id=dag_id or payload.dag_id)
    else:
        pipeline.source = payload.source
        pipeline.dag_id = dag_id or payload.dag_id or pipeline.dag_id
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)
    logger.info("pipeline_upserted", extra={"pipeline_id": str(pipeline.id), "org_id": str(org_id)})
    return pipeline


async def get_pipeline(session: AsyncSession, pipeline_id, org_id) -> Pipeline | None:
    pipeline_uuid = UUID(str(pipeline_id))
    result = await session.execute(
        select(Pipeline)
        .where(Pipeline.id == pipeline_uuid, Pipeline.org_id == org_id)
        .options(selectinload(Pipeline.dag_definition))
    )
    return result.scalar_one_or_none()


async def get_pipeline_runs(session: AsyncSession, pipeline_id, limit: int, offset: int):
    pipeline_uuid = UUID(str(pipeline_id))
    from app.models.pipeline_run import PipelineRun

    result = await session.execute(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == pipeline_uuid)
        .order_by(PipelineRun.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def upsert_dag_definition(session: AsyncSession, pipeline: Pipeline, nodes: list[dict], edges: list[dict]) -> DagDefinition:
    result = await session.execute(select(DagDefinition).where(DagDefinition.pipeline_id == pipeline.id))
    dag = result.scalar_one_or_none()
    if dag is None:
        dag = DagDefinition(pipeline_id=pipeline.id, nodes=nodes, edges=edges, updated_at=datetime.now(UTC))
    else:
        dag.nodes = nodes
        dag.edges = edges
        dag.updated_at = datetime.now(UTC)
    session.add(dag)
    await session.commit()
    await session.refresh(dag)
    return dag