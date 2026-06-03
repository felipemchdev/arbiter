from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.alert import AlertType
from app.models.pipeline import Pipeline
from app.models.pipeline_run import PipelineRun
from app.services.alert_service import check_stale_pipelines_sync, process_run_event_sync


@shared_task(name="app.workers.tasks.process_run_event")
def process_run_event(run_id: str) -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            result = await session.execute(select(PipelineRun).where(PipelineRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                return
            await process_run_event_sync(session, run)

    asyncio.run(_run())


@shared_task(name="app.workers.tasks.check_stale_pipelines")
def check_stale_pipelines() -> int:
    async def _run() -> int:
        async with async_session_maker() as session:
            return await check_stale_pipelines_sync(session)

    return asyncio.run(_run())