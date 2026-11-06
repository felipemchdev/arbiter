from __future__ import annotations

import asyncio
import logging

from celery import shared_task
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.core.database import async_session_maker
from app.models.pipeline_run import PipelineRun
from app.services.alert_service import check_stale_pipelines_sync, process_run_event_sync
from app.services.notification_service import deliver_due_alerts

logger = logging.getLogger(__name__)
MAX_RETRIES = 3
RETRY_DELAY = 60

# Retrying Exception would also swallow TypeError/AttributeError-style bugs and hide
# them behind max_retries * RETRY_DELAY of backoff, so only transient faults retry.
RETRYABLE_ERRORS = (OperationalError, RedisConnectionError, OSError)


@shared_task(
    name="app.workers.tasks.process_run_event",
    bind=True,
    autoretry_for=RETRYABLE_ERRORS,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    retry_backoff=True,
)
def process_run_event(self, run_id: str) -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            result = await session.execute(select(PipelineRun).where(PipelineRun.id == run_id).with_for_update())
            run = result.scalar_one_or_none()
            if run is None:
                logger.warning("process_run_event_run_not_found run_id=%s", run_id)
                return
            await process_run_event_sync(session, run)
            await session.commit()

    asyncio.run(_run())


@shared_task(
    name="app.workers.tasks.deliver_pending_alerts",
    bind=True,
    autoretry_for=RETRYABLE_ERRORS,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    retry_backoff=True,
)
def deliver_pending_alerts(self) -> dict:
    """Push every queued alert whose next attempt is due."""

    async def _run() -> dict:
        async with async_session_maker() as session:
            return await deliver_due_alerts(session)

    return asyncio.run(_run())


@shared_task(
    name="app.workers.tasks.check_stale_pipelines",
    bind=True,
    autoretry_for=RETRYABLE_ERRORS,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    retry_backoff=True,
)
def check_stale_pipelines(self) -> int:
    async def _run() -> int:
        async with async_session_maker() as session:
            created = await check_stale_pipelines_sync(session)
            await session.commit()
            return created

    return asyncio.run(_run())
