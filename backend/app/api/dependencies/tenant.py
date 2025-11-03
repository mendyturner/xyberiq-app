"""Tenant-related request dependencies."""

from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_settings_dependency
from app.core.security import InvalidTokenError, decode_token
from app.core.tenant import reset_current_tenant, set_current_tenant
from app.db.models import Tenant


async def get_current_tenant(
    request: Request,
    db: Session = Depends(get_db),
    settings = Depends(get_settings_dependency),
    x_tenant: str | None = Header(default=None, alias="X-Tenant"),
) -> Tenant:
    auth_header = request.headers.get("Authorization")
    bearer_token: str | None = None
    if auth_header and auth_header.lower().startswith("bearer "):
        bearer_token = auth_header.split(" ", 1)[1]

    tenant: Tenant | None = None
    payload = None
    if x_tenant:
        tenant = (
            db.execute(
                select(Tenant)
                .execution_options(tenant_aware=False)
                .where(Tenant.slug == x_tenant)
            ).scalar_one_or_none()
        )
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if bearer_token:
            try:
                payload = decode_token(bearer_token, settings=settings)
            except InvalidTokenError as exc:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
            claimed_tenant_id = payload.get("tenant_id")
            if claimed_tenant_id and str(tenant.id) != str(claimed_tenant_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
    elif bearer_token:
        try:
            payload = decode_token(bearer_token, settings=settings)
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant claim missing")
        tenant = db.get(Tenant, uuid.UUID(str(tenant_id)))
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tenant identifier")

    token = set_current_tenant(tenant.id, tenant.slug)
    try:
        yield tenant
    finally:
        reset_current_tenant(token)


__all__ = ["get_current_tenant"]
