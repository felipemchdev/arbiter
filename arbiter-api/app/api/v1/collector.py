from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

from app.api.rate_limit import rate_limit

router = APIRouter()


@router.post("/airflow/sync", deprecated=True)
@rate_limit(max_requests=60, window_seconds=60)
async def airflow_sync_alias(request: Request):
    """Deprecated — use POST /api/v1/runs/ingest instead."""
    return RedirectResponse(url="/api/v1/runs/ingest", status_code=308)
