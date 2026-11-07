from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.api.rate_limit import rate_limit
from app.api.role_guard import require_scope
from app.models.pipeline import RunStatus
from app.schemas.page import Page
from app.schemas.pipeline import PipelineRunDetail
from app.schemas.run import RunPayload, RunRead, TaskRead
from app.schemas.collector import AirflowSyncPayload
from app.services.run_service import get_run, ingest_run, list_runs, list_tasks

router = APIRouter()


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
@rate_limit(max_requests=120, window_seconds=60)
async def ingest_run_endpoint(
    request: Request,
    payload: RunPayload,
    current_org=Depends(require_scope("collector:write")),
    db: AsyncSession = Depends(get_db),
):
    """Accept one run and derive its status, duration and alerts inline."""
    return await ingest_run(db, current_org.id, payload)


@router.post("/ingest")
@rate_limit(max_requests=30, window_seconds=60)
async def ingest_batch(
    request: Request,
    payload: AirflowSyncPayload,
    current_org=Depends(require_scope("collector:write")),
    db: AsyncSession = Depends(get_db),
):
    """Accept a collector sync: one run per Airflow dag run."""
    ingested = 0
    for dag in payload.dags:
        for run in dag.runs:
            await ingest_run(
                db,
                current_org.id,
                RunPayload(
                    pipeline=dag.name,
                    source="airflow",
                    run_id=run.run_id,
                    status=run.status,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    duration_ms=run.duration_ms,
                    error_message=run.error_message,
                    dag_id=dag.dag_id,
                    nodes=dag.nodes,
                    edges=dag.edges,
                    tasks=run.tasks,
                ),
            )
            ingested += 1
    await db.commit()
    return {"ingested": ingested}


@router.get("", response_model=Page[PipelineRunDetail])
async def read_runs(
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    # "status" is the public name; the module already imports fastapi's status helper.
    run_status: RunStatus | None = Query(default=None, alias="status"),
    pipeline_id: UUID | None = Query(default=None),
    started_from: datetime | None = Query(default=None),
    started_to: datetime | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List every run of the organisation, newest started first."""
    items, total = await list_runs(
        db,
        current_org.id,
        run_status=run_status,
        pipeline_id=pipeline_id,
        started_from=started_from,
        started_to=started_to,
        query=q,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{run_id}", response_model=RunRead)
async def read_run(
    run_id: str,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    run = await get_run(db, run_id, current_org.id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return run


@router.get("/{run_id}/tasks", response_model=list[TaskRead])
async def read_run_tasks(
    run_id: str,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    return await list_tasks(db, run_id, current_org.id)
