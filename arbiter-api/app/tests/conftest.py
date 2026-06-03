from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.database import Base
from app.core.security import hash_api_key
from app.main import app
from app.models.alert import Alert
from app.models.dag_definition import DagDefinition
from app.models.organization import Organization
from app.models.pipeline import Pipeline, PipelineSource, RunStatus
from app.models.pipeline_run import PipelineRun
from app.models.task_instance import TaskInstance, TaskStatus

TEST_DB_PATH = Path("./arbiter_test.db")
TEST_DATABASE_URL = "sqlite+aiosqlite:///./arbiter_test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def override_db():
    async def _get_test_db() -> AsyncIterator[AsyncSession]:
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_instance:
        yield client_instance


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session_instance:
        yield session_instance


@pytest_asyncio.fixture
async def organization(session: AsyncSession) -> Organization:
    unique_suffix = uuid4().hex[:8]
    raw_api_key = f"arb_test_api_key_{unique_suffix}"
    organization = Organization(name=f"acme_{unique_suffix}", api_key=hash_api_key(raw_api_key))
    session.add(organization)
    await session.commit()
    await session.refresh(organization)
    organization._raw_api_key = raw_api_key  # type: ignore[attr-defined]
    return organization


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, organization: Organization) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": organization.name, "password": organization._raw_api_key},  # type: ignore[attr-defined]
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_pipeline_fixture(session: AsyncSession, organization: Organization) -> Pipeline:
    pipeline = Pipeline(org_id=organization.id, name="helios-eeip", source=PipelineSource.sdk)
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)
    return pipeline


async def create_run_fixture(session: AsyncSession, pipeline: Pipeline) -> PipelineRun:
    run = PipelineRun(
        pipeline_id=pipeline.id,
        run_id="run-1",
        status=RunStatus.failed,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        duration_ms=1000,
        error_message="boom",
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    task = TaskInstance(
        run_id=run.id,
        task_id="extract",
        status=TaskStatus.failed,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        duration_ms=1000,
        try_number=1,
        error_message="boom",
    )
    session.add(task)
    await session.commit()
    return run