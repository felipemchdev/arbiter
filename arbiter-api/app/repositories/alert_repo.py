from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertType


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_alerts(
        self,
        org_id,
        *,
        alert_type: AlertType | None = None,
        resolved: bool | None = None,
        pipeline_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Alert], int]:
        """Page through the alerts of one organisation.

        An absent ``resolved`` filter keeps the previous behaviour: open alerts only.
        """
        filters = [Alert.resolved == (False if resolved is None else resolved)]
        if alert_type is not None:
            filters.append(Alert.type == alert_type)
        if pipeline_id is not None:
            filters.append(Alert.pipeline_id == pipeline_id)
        filters.append(Alert.pipeline.has(org_id=org_id))
        total_result = await self.session.execute(
            select(func.count()).select_from(Alert).join(Alert.pipeline).where(*filters)
        )
        result = await self.session.execute(
            select(Alert)
            .join(Alert.pipeline)
            .where(*filters)
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total_result.scalar_one()

    async def get_by_id(self, alert_id, org_id):
        try:
            alert_uuid = UUID(str(alert_id))
        except ValueError:
            return None  # malformed UUID -> caller answers 404 instead of a 500
        result = await self.session.execute(
            select(Alert).join(Alert.pipeline).where(Alert.id == alert_uuid, Alert.pipeline.has(org_id=org_id))
        )
        return result.scalar_one_or_none()