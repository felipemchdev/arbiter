from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app.models  # noqa: F401
from app.core.config import settings
from app.models.alert import Alert, AlertType
from app.models.alert_delivery import AlertDelivery, AlertDeliveryStatus
from app.models.notification_channel import NotificationChannel
from app.models.organization import Organization
from app.models.pipeline import Pipeline, PipelineSource
from app.services import pipeline_service

pytestmark = [pytest.mark.asyncio, pytest.mark.postgresql]


@pytest.mark.skipif(
    not settings.database_url.startswith("postgresql"),
    reason="this regression needs a PostgreSQL database set by DATABASE_URL",
)
async def test_deleting_a_pipeline_on_postgresql_removes_its_delivery_rows():
    """The migration-created schema must accept the delete the ORM cascade orders.

    The database is the one `alembic upgrade head` built, so the keys and the
    index the revisions declare are the ones under test. Everything the test
    writes is rolled back with the outer transaction.
    """
    suffix = uuid.uuid4().hex[:8]
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            outer = await connection.begin()
            try:
                async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                    org = Organization(name=f"pg-delete-{suffix}")
                    session.add(org)
                    await session.flush()
                    pipeline = Pipeline(org_id=org.id, name=f"pg_etl_{suffix}", source=PipelineSource.sdk)
                    session.add(pipeline)
                    await session.flush()
                    now = datetime.now(UTC)
                    channels = [
                        NotificationChannel(
                            org_id=org.id,
                            name=f"pg-channel-{index}",
                            url=f"https://hook{index}.example.test/arbiter",
                            signing_secret="arbwhk_test",
                            enabled=True,
                        )
                        for index in range(2)
                    ]
                    session.add_all(channels)
                    alert = Alert(
                        pipeline_id=pipeline.id,
                        type=AlertType.failure,
                        message=f"run failed {suffix}",
                        resolved=False,
                        created_at=now,
                    )
                    session.add(alert)
                    await session.flush()
                    session.add_all(
                        [
                            AlertDelivery(
                                alert_id=alert.id,
                                channel_id=channels[0].id,
                                status=AlertDeliveryStatus.pending,
                            ),
                            AlertDelivery(
                                alert_id=alert.id,
                                channel_id=channels[1].id,
                                status=AlertDeliveryStatus.delivered,
                                delivered_at=now,
                                response_status_code=200,
                            ),
                        ]
                    )
                    await session.flush()
                    org_id = org.id
                    pipeline_id = str(pipeline.id)

                    deleted = await pipeline_service.delete_pipeline(session, pipeline_id, org_id)

                    assert deleted is True
                    assert (await session.scalars(select(AlertDelivery))).all() == []
                    assert (await session.scalars(select(Alert))).all() == []
            finally:
                await outer.rollback()
    finally:
        await engine.dispose()
