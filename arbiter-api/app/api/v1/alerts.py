from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.api.role_guard import require_owner
from app.models.alert import AlertType
from app.schemas.alert import AlertRead, AlertResolveResponse
from app.schemas.page import Page
from app.services.alert_service import resolve_alert
from app.repositories.alert_repo import AlertRepository

router = APIRouter()


@router.get("", response_model=Page[AlertRead])
async def read_alerts(
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    alert_type: AlertType | None = Query(default=None, alias="type"),
    resolved: bool | None = Query(default=None),
    pipeline_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List alerts, open ones by default.

    Pass ``resolved=true`` to read the alerts an owner already resolved.
    """
    repository = AlertRepository(db)
    items, total = await repository.list_alerts(
        current_org.id,
        alert_type=alert_type,
        resolved=resolved,
        pipeline_id=pipeline_id,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.put("/{alert_id}/resolve", response_model=AlertResolveResponse)
async def resolve_alert_endpoint(
    alert_id: str,
    current_org=Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    repository = AlertRepository(db)
    alert = await repository.get_by_id(alert_id, current_org.id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
    await resolve_alert(db, alert)
    return AlertResolveResponse()
