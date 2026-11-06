from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dag_definition import DagDefinition
from app.models.pipeline import Pipeline, RunStatus
from app.schemas.pipeline import PipelineCreate, PipelineUpdate

logger = logging.getLogger(__name__)


async def list_pipelines(
    session: AsyncSession,
    org_id,
    *,
    run_status: RunStatus | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Pipeline], int]:
    """Page through the pipelines of one organisation, newest created first."""
    conditions = [Pipeline.org_id == org_id]
    if run_status is not None:
        conditions.append(Pipeline.last_run_status == run_status)
    if query:
        # lower() + like() instead of ilike keeps this portable across SQLite and PostgreSQL.
        pattern = f"%{query.lower()}%"
        conditions.append(
            or_(
                func.lower(Pipeline.name).like(pattern),
                func.lower(Pipeline.dag_id).like(pattern),
            )
        )

    total_result = await session.execute(
        select(func.count()).select_from(Pipeline).where(*conditions)
    )
    result = await session.execute(
        select(Pipeline)
        .where(*conditions)
        .order_by(Pipeline.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all()), total_result.scalar_one()


async def create_pipeline(session: AsyncSession, org_id, payload: PipelineCreate, dag_id: str | None = None) -> Pipeline:
    result = await session.execute(
        select(Pipeline).where(Pipeline.org_id == org_id, Pipeline.name == payload.name)
    )
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        pipeline = Pipeline(
            org_id=org_id,
            name=payload.name,
            source=payload.source,
            dag_id=dag_id or payload.dag_id,
            slow_threshold_ms=payload.slow_threshold_ms,
        )
    else:
        pipeline.source = payload.source
        pipeline.dag_id = dag_id or payload.dag_id or pipeline.dag_id
        # Run ingest reuses this function without a threshold; only an explicit
        # value may change the budget, so a plain ingest never wipes it.
        if payload.slow_threshold_ms is not None:
            pipeline.slow_threshold_ms = payload.slow_threshold_ms
    session.add(pipeline)
    await session.flush()
    logger.debug("pipeline_staged", extra={"pipeline_id": str(pipeline.id), "org_id": str(org_id)})
    return pipeline


async def get_pipeline(session: AsyncSession, pipeline_id, org_id) -> Pipeline | None:
    try:
        pipeline_uuid = UUID(str(pipeline_id))
    except ValueError:
        return None
    result = await session.execute(
        select(Pipeline)
        .where(Pipeline.id == pipeline_uuid, Pipeline.org_id == org_id)
        .options(selectinload(Pipeline.dag_definition))
    )
    return result.scalar_one_or_none()


async def update_pipeline(session: AsyncSession, pipeline_id, org_id, payload: PipelineUpdate) -> Pipeline | None:
    """Apply only the fields present in the payload; a null threshold clears the budget."""
    pipeline = await get_pipeline(session, pipeline_id, org_id)
    if pipeline is None:
        return None
    if "slow_threshold_ms" in payload.model_fields_set:
        pipeline.slow_threshold_ms = payload.slow_threshold_ms
    session.add(pipeline)
    await session.flush()
    return pipeline


async def get_pipeline_runs(session: AsyncSession, pipeline_id, limit: int, offset: int):
    try:
        pipeline_uuid = UUID(str(pipeline_id))
    except ValueError:
        return [], 0
    from app.models.pipeline_run import PipelineRun

    total_result = await session.execute(
        select(func.count()).select_from(PipelineRun).where(PipelineRun.pipeline_id == pipeline_uuid)
    )
    result = await session.execute(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == pipeline_uuid)
        .order_by(PipelineRun.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all()), total_result.scalar_one()


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
    return dag

async def delete_pipeline(db: AsyncSession, pipeline_id: str, org_id) -> bool:
    from uuid import UUID as _UUID

    try:
        pid = _UUID(pipeline_id)
    except ValueError:
        return False
    result = await db.execute(select(Pipeline).where(Pipeline.id == pid, Pipeline.org_id == org_id))
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        return False
    await db.delete(pipeline)
    await db.commit()
    return True
