"""Audit logging service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditLog


class AuditService:
    """Utility helpers for recording audit trail entries."""

    @staticmethod
    def log(
        *,
        db: Session,
        tenant_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        action: str,
        target_type: str | None = None,
        target_id: str | None = None,
        meta: dict[str, Any] | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            meta=meta,
            ip=ip,
            user_agent=user_agent,
        )
        db.add(entry)
        return entry


__all__ = ["AuditService"]
