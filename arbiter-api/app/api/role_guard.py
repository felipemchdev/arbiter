from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_org
from app.models.organization import Organization


def require_owner(org: Organization = Depends(get_current_org)) -> Organization:
    role = getattr(org, "_role", "viewer")
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return org


def require_scope(*required: str):
    """Allow a route only for principals whose API key actually carries one of `required`.

    JWT-authenticated users have no API key scope set and are governed by their role
    in `require_owner`; this guard exists to stop collector-scoped keys, which used to
    be implicitly promoted to owner, from reaching owner-only routes.
    """

    def dependency(org: Organization = Depends(get_current_org)) -> Organization:
        granted = getattr(org, "_api_key_scopes", None)
        if granted is not None and not set(required) & set(granted):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"api key missing scope: {' or '.join(required)}",
            )
        return org

    return dependency
