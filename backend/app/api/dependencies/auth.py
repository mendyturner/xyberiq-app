"""Authentication related dependencies."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_settings_dependency
from app.api.dependencies.tenant import get_current_tenant
from app.core.config import Settings
from app.core.security import InvalidTokenError, decode_token
from app.core.tenant import tenant_context
from app.db.models import Tenant, User, UserStatus
from app.services.users import UserService


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
    return auth_header.split(" ", 1)[1].strip()


def get_current_user(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> User:
    token = _extract_bearer_token(request)
    try:
        payload = decode_token(token, settings=settings)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if payload.get("scope") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope")
    if payload.get("tenant_id") != str(tenant.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    with tenant_context(tenant.id, tenant.slug):
        user = UserService.get_by_id(db=db, user_id=uuid.UUID(str(user_id)))

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    return user


__all__ = ["get_current_user"]
