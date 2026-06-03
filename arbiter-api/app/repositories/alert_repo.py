from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self, org_id):
        result = await self.session.execute(
            select(Alert)
            .join(Alert.pipeline)
            .where(Alert.resolved.is_(False), Alert.pipeline.has(org_id=org_id))
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, alert_id, org_id):
        alert_uuid = UUID(str(alert_id))
        result = await self.session.execute(
            select(Alert).join(Alert.pipeline).where(Alert.id == alert_uuid, Alert.pipeline.has(org_id=org_id))
        )
        return result.scalar_one_or_none()