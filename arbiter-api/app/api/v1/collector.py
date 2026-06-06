from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

router = APIRouter()


@router.post("/airflow/sync", deprecated=True)
async def airflow_sync_alias(request: Request):
    """Deprecated — use POST /api/v1/runs/ingest instead."""
    return RedirectResponse(url="/api/v1/runs/ingest", status_code=308)
