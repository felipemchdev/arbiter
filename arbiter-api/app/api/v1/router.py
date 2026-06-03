from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.collector import router as collector_router
from app.api.v1.health import router as health_router
from app.api.v1.pipelines import router as pipelines_router
from app.api.v1.runs import router as runs_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(pipelines_router, prefix="/pipelines", tags=["pipelines"])
router.include_router(runs_router, prefix="/runs", tags=["runs"])
router.include_router(collector_router, prefix="/collector", tags=["collector"])
router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
router.include_router(health_router, tags=["health"])
