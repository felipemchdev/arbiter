from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.core.redis import redis_client
from app.models.pipeline import Pipeline, RunStatus
from app.models.pipeline_run import PipelineRun
from app.services.pipeline_service import list_pipelines

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = True
    redis_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    try:
        await redis_client.ping()
    except Exception:  # noqa: BLE001
        redis_ok = False
    return {"status": "ok", "db": db_ok, "redis": redis_ok}


@router.get("/metrics")
async def metrics(current_org=Depends(get_current_org), db: AsyncSession = Depends(get_db)):
    today = datetime.now(UTC).date()
    pipelines = await list_pipelines(db, current_org.id)
    run_result = await db.execute(
        text(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
            FROM pipeline_runs pr
            JOIN pipelines p ON p.id = pr.pipeline_id
            WHERE p.org_id = :org_id AND DATE(pr.started_at) = :today
            """
        ),
        {"org_id": str(current_org.id), "today": today},
    )
    row = run_result.first()
    total_runs = int(row.total or 0) if row else 0
    failed_runs = int(row.failed or 0) if row else 0
    active_pipelines = len([pipeline for pipeline in pipelines if pipeline.last_run_status != RunStatus.failed])
    avg_duration_result = await db.execute(
        text(
            """
            SELECT AVG(duration_ms) AS avg_duration
            FROM pipeline_runs pr
            JOIN pipelines p ON p.id = pr.pipeline_id
            WHERE p.org_id = :org_id AND DATE(pr.started_at) = :today
            """
        ),
        {"org_id": str(current_org.id), "today": today},
    )
    avg_row = avg_duration_result.first()
    return {
        "runs_today": total_runs,
        "failed_today": failed_runs,
        "active_pipelines": active_pipelines,
        "avg_duration_ms": float(avg_row.avg_duration or 0) if avg_row else 0,
    }