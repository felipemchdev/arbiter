from __future__ import annotations

import logging
import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertType
from app.core.config import settings
from app.models.pipeline import Pipeline, RunStatus
from app.models.pipeline_run import PipelineRun
from app.services.notification_service import queue_alert_deliveries

logger = logging.getLogger(__name__)

# A skipped run still reports a duration, so it belongs in the budget check.
TERMINAL_RUN_STATUSES = frozenset({RunStatus.success, RunStatus.failed, RunStatus.skipped})
DURATION_BASELINE_PERCENTILE = 95


async def create_alert(
    session: AsyncSession,
    *,
    pipeline_id,
    alert_type: AlertType,
    message: str,
    run_id=None,
) -> Alert | None:
    """Record one alert. Return None when a partial unique index already covers it.

    Deduplication happens in the database, so no worker needs a check that races.
    A rejected alert queues no delivery. The savepoint must be open before the alert
    is added: SQLAlchemy can flush pending state when a nested transaction starts,
    and an IntegrityError raised by that flush would escape the handling below.
    """
    alert = Alert(pipeline_id=pipeline_id, run_id=run_id, type=alert_type, message=message, resolved=False)
    try:
        async with session.begin_nested():
            session.add(alert)
            await session.flush()
    except IntegrityError:
        if alert in session:
            session.expunge(alert)
        logger.debug(
            "alert_already_exists_skipped pipeline_id=%s type=%s",
            pipeline_id, alert_type.value,
        )
        return None
    await queue_alert_deliveries(session, alert)
    logger.info("alert_created", extra={"pipeline_id": str(pipeline_id), "type": alert_type.value})
    return alert


async def resolve_alert(session: AsyncSession, alert: Alert) -> Alert:
    alert.resolved = True
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    logger.info("alert_resolved", extra={"alert_id": str(alert.id)})
    return alert


def _nearest_rank_percentile(values: list[int], percentile: float) -> int:
    """Return the smallest sample that at least `percentile`% of samples do not exceed."""
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile / 100 * len(ordered)))
    return ordered[rank - 1]


async def _duration_budget_ms(session: AsyncSession, *, pipeline: Pipeline, run: PipelineRun) -> int | None:
    """Budget for this run: the owner's threshold, else the p95 of recent successful runs."""
    if pipeline.slow_threshold_ms is not None:
        return pipeline.slow_threshold_ms

    result = await session.execute(
        select(PipelineRun.duration_ms)
        .where(
            PipelineRun.pipeline_id == pipeline.id,
            PipelineRun.status == RunStatus.success,
            PipelineRun.duration_ms.is_not(None),
            PipelineRun.id != run.id,
        )
        .order_by(PipelineRun.started_at.desc())
        .limit(settings.duration_baseline_samples)
    )
    durations = [int(value) for value in result.scalars().all() if value is not None]
    if len(durations) < settings.duration_baseline_min_samples:
        return None
    return _nearest_rank_percentile(durations, DURATION_BASELINE_PERCENTILE)


async def maybe_create_duration_alert(
    session: AsyncSession, *, run: PipelineRun, pipeline: Pipeline | None
) -> Alert | None:
    """Create a duration_exceeded alert when a terminal run goes over its budget."""
    if pipeline is None or run.duration_ms is None:
        return None
    if run.status not in TERMINAL_RUN_STATUSES:
        return None
    budget_ms = await _duration_budget_ms(session, pipeline=pipeline, run=run)
    if budget_ms is None or run.duration_ms <= budget_ms:
        return None
    return await create_alert(
        session,
        pipeline_id=run.pipeline_id,
        run_id=run.id,
        alert_type=AlertType.duration_exceeded,
        message=f"Run {run.run_id} took {run.duration_ms}ms, over the {budget_ms}ms budget",
    )


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

    await maybe_create_duration_alert(session, run=run, pipeline=pipeline)

    await session.flush()
    logger.info("run_processed", extra={"run_id": str(run.id), "status": run.status.value})


async def check_stale_pipelines_sync(session: AsyncSession) -> int:
    cutoff = datetime.now(UTC) - timedelta(hours=settings.stale_pipeline_hours)

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
            Pipeline.created_at < cutoff,
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
            message=f"No runs for pipeline {pipeline.name} in the last {settings.stale_pipeline_hours} hours",
        )
        if alert is not None:
            created += 1
    return created
