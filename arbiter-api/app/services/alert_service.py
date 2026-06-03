from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertType
from app.models.pipeline import Pipeline, RunStatus
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
    existing = await session.execute(
        select(Alert).where(
            Alert.pipeline_id == pipeline_id,
            Alert.type == alert_type,
            Alert.resolved.is_(False),
            Alert.run_id == run_id,
            Alert.message == message,
        )
    )
    if existing.scalar_one_or_none():
        return None

    alert = Alert(pipeline_id=pipeline_id, run_id=run_id, type=alert_type, message=message, resolved=False)
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    logger.info("alert_created", extra={"alert_id": str(alert.id), "pipeline_id": str(pipeline_id), "type": alert_type.value})
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

    if run.status == RunStatus.failed:
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
    result = await session.execute(select(Pipeline))
    created = 0
    for pipeline in result.scalars().all():
        latest_result = await session.execute(
            select(PipelineRun).where(PipelineRun.pipeline_id == pipeline.id).order_by(PipelineRun.started_at.desc()).limit(1)
        )
        latest_run = latest_result.scalar_one_or_none()
        if latest_run is None or (latest_run.started_at and latest_run.started_at < cutoff):
            alert = await create_alert(
                session,
                pipeline_id=pipeline.id,
                alert_type=AlertType.no_run,
                message=f"No runs for pipeline {pipeline.name} in the last 24 hours",
            )
            if alert is not None:
                created += 1
    return created