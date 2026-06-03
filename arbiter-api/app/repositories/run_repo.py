from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert, AlertType
from app.models.pipeline_run import PipelineRun
from app.models.task_instance import TaskInstance


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, run_id, org_id):
        result = await self.session.execute(
            select(PipelineRun)
            .join(PipelineRun.pipeline)
            .where(PipelineRun.id == run_id, PipelineRun.pipeline.has(org_id=org_id))
            .options(selectinload(PipelineRun.task_instances))
        )
        return result.scalar_one_or_none()

    async def get_by_native_run_id(self, pipeline_id, native_run_id):
        result = await self.session.execute(
            select(PipelineRun).where(PipelineRun.pipeline_id == pipeline_id, PipelineRun.run_id == native_run_id)
        )
        return result.scalar_one_or_none()

    async def list_by_pipeline(self, pipeline_id, limit: int = 50, offset: int = 0):
        result = await self.session.execute(
            select(PipelineRun)
            .where(PipelineRun.pipeline_id == pipeline_id)
            .order_by(PipelineRun.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_tasks(self, run_uuid):
        result = await self.session.execute(
            select(TaskInstance).where(TaskInstance.run_id == run_uuid).order_by(TaskInstance.started_at.asc())
        )
        return list(result.scalars().all())

    async def latest_run_time_for_pipeline(self, pipeline_id):
        result = await self.session.execute(
            select(func.max(PipelineRun.started_at)).where(PipelineRun.pipeline_id == pipeline_id)
        )
        return result.scalar_one_or_none()

    async def unresolved_alert_exists(self, pipeline_id, alert_type: AlertType, run_id=None):
        stmt = select(Alert).where(
            Alert.pipeline_id == pipeline_id,
            Alert.type == alert_type,
            Alert.resolved.is_(False),
        )
        if run_id is not None:
            stmt = stmt.where(Alert.run_id == run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None