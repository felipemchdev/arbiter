from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertType
from app.models.pipeline import Pipeline
from app.models.pipeline_run import PipelineRun

logger = logging.getLogger(__name__)


async def create_alert(
    session: AsyncSession,
    *,
    pipeline_id,
    alert_type: AlertType,
    message: str,
    run_id=None,
) -> Alert | None:
    # Do not use SELECT-then-INSERT: that check is not atomic under concurrent workers.
    # The partial unique index (uq_active_alert) guarantees atomicity at the DB level.
    # If two workers race, the second INSERT raises IntegrityError and we return None.
    alert = Alert(pipeline_id=pipeline_id, run_id=run_id, type=alert_type, message=message, resolved=False)
    session.add(alert)
    try:
        await session.flush()  # let the unique constraint fire before full commit
    except IntegrityError:
        await session.rollback()
        logger.debug(
            "alert_already_exists_skipped pipeline_id=%s type=%s",
            pipeline_id, alert_type.value,
        )
        return None
    logger.info("alert_created", extra={"pipeline_id": str(pipeline_id), "type": alert_type.value})
    return alert


async def resolve_alert(session: AsyncSession, alert: Alert) -> Alert:
    alert.resolved = True
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    logger.info("alert_resolved", extra={"alert_id": str(alert.id)})
    return alert


async def process_run_event_sync(session: AsyncSession, run: PipelineRun) -> None:
    if run.finished_at and run.started_at and run.duration_ms is None:
        run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)

    pipeline_result = await session.execute(select(Pipeline).where(Pipeline.id == run.pipeline_id))
    pipeline = pipeline_result.scalar_one_or_none()
    if pipeline is not None:
        pipeline.last_run_status = run.status
        pipeline.last_run_at = run.finished_at or run.started_at
        session.add(pipeline)
    session.add(run)

    if run.status.value == "failed":
        await create_alert(
            session,
            pipeline_id=run.pipeline_id,
            run_id=run.id,
            alert_type=AlertType.failure,
            message=f"Run {run.run_id} failed",
        )

    await session.commit()
    logger.info("run_processed", extra={"run_id": str(run.id), "status": run.status.value})


async def check_stale_pipelines_sync(session: AsyncSession) -> int:
    cutoff = datetime.now(UTC) - timedelta(hours=24)

    latest_run_subq = (
        select(
            PipelineRun.pipeline_id,
            func.max(PipelineRun.started_at).label("latest_started"),
        )
        .group_by(PipelineRun.pipeline_id)
        .subquery("latest_runs")
    )

    stale_pipelines = await session.execute(
        select(Pipeline)
        .outerjoin(
            latest_run_subq,
            Pipeline.id == latest_run_subq.c.pipeline_id,
        )
        .where(
            Pipeline.created_at < datetime.now(UTC) - timedelta(hours=24),
            (latest_run_subq.c.latest_started.is_(None))
            | (latest_run_subq.c.latest_started < cutoff)
        )
    )

    created = 0
    for pipeline in stale_pipelines.scalars().all():
        alert = await create_alert(
            session,
            pipeline_id=pipeline.id,
            alert_type=AlertType.no_run,
            message=f"No runs for pipeline {pipeline.name} in the last 24 hours",
        )
        if alert is not None:
            created += 1
    return created
