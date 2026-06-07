from contextlib import asynccontextmanager
import logging
from pathlib import Path

from alembic.config import Config as AlembicConfig
from alembic import command
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import install_exception_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = AlembicConfig(str(alembic_ini))
    # Lock-based migration guard: only one replica runs migrations.
    # Uses a database-level advisory lock to serialize startup.
    try:
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import text
        from app.core.database import async_session_maker
        async with async_session_maker() as session:
            await session.execute(text("SELECT pg_advisory_lock(1234567890)"))
            try:
                await session.run_sync(lambda conn: command.upgrade(alembic_cfg, "head"))
            finally:
                await session.execute(text("SELECT pg_advisory_unlock(1234567890)"))
    except sqlalchemy.exc.OperationalError:
        # Non-PostgreSQL or lock failure: fall back to direct upgrade
        command.upgrade(alembic_cfg, "head")
    yield


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="Pipeline observability — ingest-first monitoring for data pipelines. Receives run events via HTTP and provides DAG visualization, metrics, and alerts.",
    contact={"name": "Felipe Machado", "url": "https://github.com/felipemchdev/arbiter"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_exception_handlers(app)
app.include_router(v1_router, prefix=settings.api_v1_str)
