from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core import PydanticCustomError

API_KEY_ENVIRONMENTS = ("production", "staging", "test", "development")
API_KEY_SCOPES = ("collector:write", "pipeline:read", "org:admin")


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime


class ApiKeyCreateRequest(BaseModel):
    name: str
    environment: str = "production"
    scopes: str = "collector:write"

    # PydanticCustomError, not ValueError: FastAPI puts the validator exception object
    # into the 422 body's ctx, which is not JSON serialisable.
    @field_validator("environment")
    @classmethod
    def _check_environment(cls, v: str) -> str:
        if v not in API_KEY_ENVIRONMENTS:
            raise PydanticCustomError(
                "invalid_environment",
                "invalid environment {value}. allowed: {allowed}",
                {"value": v, "allowed": ", ".join(API_KEY_ENVIRONMENTS)},
            )
        return v

    @field_validator("scopes")
    @classmethod
    def _check_scopes(cls, v: str) -> str:
        requested = {scope.strip() for scope in v.split(",") if scope.strip()}
        if not requested:
            raise PydanticCustomError("empty_scopes", "scopes must contain at least one scope")
        unknown = sorted(requested - set(API_KEY_SCOPES))
        if unknown:
            raise PydanticCustomError(
                "invalid_scope",
                "invalid scope(s) {value}. allowed: {allowed}",
                {"value": ", ".join(unknown), "allowed": ", ".join(API_KEY_SCOPES)},
            )
        return ",".join(sorted(requested))


class ApiKeyCreateResponse(BaseModel):
    api_key: str
    prefix: str
    id: UUID


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    environment: str
    prefix: str
    scopes: str
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool
    expires_at: datetime | None
