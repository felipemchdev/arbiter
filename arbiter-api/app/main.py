from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import install_exception_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://arbiter-dashboard.wonderfulbush-04a41aac.eastus.azurecontainerapps.io","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["Authorization","Content-Type","X-API-Key"],
)
install_exception_handlers(app)
app.include_router(v1_router, prefix=settings.api_v1_str)