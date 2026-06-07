from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.api.rate_limit import rate_limit
from app.schemas.run import RunPayload, RunRead, TaskRead
from app.schemas.collector import AirflowSyncPayload
from app.services.run_service import get_run, ingest_run, list_tasks

router = APIRouter()


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
@rate_limit(max_requests=120, window_seconds=60)
async def ingest_run_endpoint(
    payload: RunPayload,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    return await ingest_run(db, current_org.id, payload)


@router.post("/ingest")
@rate_limit(max_requests=30, window_seconds=60)
async def ingest_batch(
    payload: AirflowSyncPayload,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
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
