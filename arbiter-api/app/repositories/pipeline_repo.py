from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dag_definition import DagDefinition
from app.models.pipeline import Pipeline


class PipelineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_org(self, org_id):
        result = await self.session.execute(
            select(Pipeline).where(Pipeline.org_id == org_id).order_by(Pipeline.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, pipeline_id, org_id):
        result = await self.session.execute(
            select(Pipeline)
            .where(Pipeline.id == pipeline_id, Pipeline.org_id == org_id)
            .options(selectinload(Pipeline.dag_definition))
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, org_id):
        result = await self.session.execute(select(Pipeline).where(Pipeline.name == name, Pipeline.org_id == org_id))
        return result.scalar_one_or_none()

    async def get_by_dag_id(self, dag_id: str, org_id):
        result = await self.session.execute(select(Pipeline).where(Pipeline.dag_id == dag_id, Pipeline.org_id == org_id))
        return result.scalar_one_or_none()

    async def get_dag_definition(self, pipeline_id):
        result = await self.session.execute(select(DagDefinition).where(DagDefinition.pipeline_id == pipeline_id))
        return result.scalar_one_or_none()