from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import install_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("lifespan startup")
    yield

    logger.info("lifespan shutdown")


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description=(
        "Pipeline observability - ingest-first monitoring for data pipelines. "
        "Receives run events via HTTP and provides DAG visualization, metrics, "
        "and alerts."
    ),
    contact={
        "name": "Felipe Machado",
        "url": "https://github.com/felipemchdev/arbiter",
    },
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

app.include_router(
    v1_router,
    prefix=settings.api_v1_str,
)

logger.info("app: initialization completed")
