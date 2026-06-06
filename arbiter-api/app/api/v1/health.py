from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import cast, Date, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.core.redis import redis_client
from app.models.pipeline import Pipeline, RunStatus
from app.models.pipeline_run import PipelineRun

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
    count_result = await db.execute(
        select(func.count()).select_from(Pipeline)
        .where(Pipeline.org_id == current_org.id, Pipeline.last_run_status != RunStatus.failed)
    )
    active_pipelines = count_result.scalar_one()
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


@@router.get("/metrics/runs-per-day")
async def runs_per_day(
    days: int = Query(default=7, ge=1, le=90),
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(UTC) - timedelta(days=days)

    result = await db.execute(
        select(
            cast(PipelineRun.started_at, Date).label("day"),
            func.count(PipelineRun.id).label("count"),
            func.sum(
                func.case(
                    (PipelineRun.status == RunStatus.failed, 1),
                    else_=0,
                )
            ).label("failed"),
        )
        .join(Pipeline, PipelineRun.pipeline_id == Pipeline.id)
        .where(
            Pipeline.org_id == current_org.id,
            PipelineRun.started_at >= since,
        )
        .group_by(cast(PipelineRun.started_at, Date))
        .order_by(cast(PipelineRun.started_at, Date).asc())
    )
    rows = result.all()

    row_map = {row.day: {"count": int(row.count), "failed": int(row.failed or 0)} for row in rows}
    output = []
    for i in range(days):
        d = (datetime.now(UTC) - timedelta(days=days - 1 - i)).date()
        output.append({
            "date": d.isoformat(),
            "label": d.strftime("%b %d"),
            "count": row_map.get(d, {}).get("count", 0),
            "failed": row_map.get(d, {}).get("failed", 0),
        })

    return {"data": output, "days": days}
