from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_org, get_db
from app.models.alert import Alert
from app.schemas.alert import AlertRead, AlertResolveResponse
from app.services.alert_service import resolve_alert
from app.repositories.alert_repo import AlertRepository

router = APIRouter()


@router.get("", response_model=list[AlertRead])
async def read_alerts(
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    repository = AlertRepository(db)
    return await repository.list_active(current_org.id, limit=limit, offset=offset)


@router.put("/{alert_id}/resolve", response_model=AlertResolveResponse)
async def resolve_alert_endpoint(
    alert_id: str,
    current_org=Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    repository = AlertRepository(db)
    alert = await repository.get_by_id(alert_id, current_org.id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
    await resolve_alert(db, alert)
    return AlertResolveResponse()
