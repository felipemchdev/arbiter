from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.alert import AlertType
from app.models.pipeline import Pipeline
from app.models.pipeline_run import PipelineRun
from app.services.alert_service import check_stale_pipelines_sync, process_run_event_sync

logger = logging.getLogger(__name__)
MAX_RETRIES = 3
RETRY_DELAY = 60


@shared_task(
    name="app.workers.tasks.process_run_event",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
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

    asyncio.run(_run())


@shared_task(
    name="app.workers.tasks.check_stale_pipelines",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    retry_backoff=True,
)
def check_stale_pipelines(self) -> int:
    async def _run() -> int:
        async with async_session_maker() as session:
            return await check_stale_pipelines_sync(session)

    return asyncio.run(_run())
