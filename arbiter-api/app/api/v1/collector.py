from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.schemas.collector import AirflowSyncPayload
from app.services.run_service import ingest_run
from app.schemas.run import RunPayload

router = APIRouter()


@router.post("/airflow/sync")
async def airflow_sync(
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
    return {"ingested": ingested}
