from fastapi import HTTPException, Depends, status

from app.api.deps import get_current_org
from app.models.organization import Organization


def require_owner(org: Organization = Depends(get_current_org)) -> Organization:
    role = getattr(org, "_role", "viewer")
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return org
