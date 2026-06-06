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
    command.upgrade(alembic_cfg, "head")
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_exception_handlers(app)
app.include_router(v1_router, prefix=settings.api_v1_str)
