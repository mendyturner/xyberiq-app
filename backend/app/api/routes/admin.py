"""Admin portal endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.tenant import get_current_tenant
from app.core.tenant import tenant_context
from app.db.models import (
    Assignment,
    AssignmentStatus,
    Event,
    Module,
    Tenant,
    User,
    UserStatus,
    UserRole,
)
from app.db.models.enums import RoleKey
from app.schemas import UserOut

router = APIRouter(prefix="/admin", tags=["Admin"])


def _ensure_admin(user: User) -> None:
    role_keys = {user_role.role.key for user_role in user.roles if user_role.role is not None}
    if RoleKey.ADMIN not in role_keys:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")


def _serialize_user(user: User) -> UserOut:
    roles = [user_role.role.key for user_role in user.roles if user_role.role is not None]
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        status=user.status,
        roles=roles,
    )


@router.get("/dashboard")
def tenant_dashboard(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_admin(current_user)

    with tenant_context(tenant.id, tenant.slug):
        active_users = db.execute(
            select(func.count(User.id)).where(User.tenant_id == tenant.id, User.status == UserStatus.ACTIVE)
        ).scalar_one() or 0
        completed_assignments = db.execute(
            select(func.count(Assignment.id)).where(
                Assignment.tenant_id == tenant.id, Assignment.status == AssignmentStatus.COMPLETED
            )
        ).scalar_one() or 0
        in_progress_assignments = db.execute(
            select(func.count(Assignment.id)).where(
                Assignment.tenant_id == tenant.id, Assignment.status == AssignmentStatus.IN_PROGRESS
            )
        ).scalar_one() or 0
        overdue_assignments = db.execute(
            select(func.count(Assignment.id)).where(
                Assignment.tenant_id == tenant.id, Assignment.status == AssignmentStatus.OVERDUE
            )
        ).scalar_one() or 0

        completions_by_module = db.execute(
            select(Module.title, func.count(Assignment.id))
            .join(Assignment, Assignment.module_id == Module.id)
            .where(Assignment.tenant_id == tenant.id, Assignment.status == AssignmentStatus.COMPLETED)
            .group_by(Module.id, Module.title)
            .order_by(func.count(Assignment.id).desc())
        ).all()

        recent_events = (
            db.execute(
                select(Event)
                .where(Event.tenant_id == tenant.id)
                .order_by(Event.occurred_at.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

    return {
        "summary": {
            "active_users": active_users,
            "completed_assignments": completed_assignments,
            "in_progress_assignments": in_progress_assignments,
            "overdue_assignments": overdue_assignments,
        },
        "completions_by_module": [
            {"module_title": title, "completed_count": int(count)} for title, count in completions_by_module
        ],
        "recent_activity": [
            {
                "event_type": event.event_type.value if event.event_type else None,
                "occurred_at": event.occurred_at,
                "user_id": str(event.user_id) if event.user_id else None,
            }
            for event in recent_events
        ],
        "trial": {
            "status": tenant.subscription_status,
            "trial_ends_at": tenant.trial_ends_at,
            "plan_code": tenant.plan_code,
        },
    }


@router.get("/employees")
def list_employees(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_admin(current_user)

    with tenant_context(tenant.id, tenant.slug):
        employees = (
            db.execute(
                select(User)
                .where(User.tenant_id == tenant.id)
                .options(selectinload(User.roles).selectinload(UserRole.role))
                .order_by(User.last_name, User.first_name)
            )
            .scalars()
            .all()
        )

    return {"employees": [_serialize_user(user) for user in employees]}


@router.get("/training/catalog")
def training_catalog(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_admin(current_user)

    modules = (
        db.execute(
            select(Module)
            .options(selectinload(Module.contents))
            .order_by(Module.title)
        )
        .scalars()
        .all()
    )

    return {
        "modules": [
            {
                "id": str(module.id),
                "title": module.title,
                "code": module.code,
                "duration_minutes": module.duration_minutes,
                "content_versions": [
                    {
                        "id": str(content.id),
                        "version": content.version,
                        "content_type": content.content_type.value if content.content_type else None,
                        "uri": content.uri,
                        "is_published": content.is_published,
                    }
                    for content in module.contents
                ],
            }
            for module in modules
        ]
    }


@router.post("/exports/completions", status_code=status.HTTP_202_ACCEPTED)
def request_completions_export(
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_admin(current_user)
    # Placeholder: actual export processing to be implemented in Phase 2.
    return {
        "detail": "Export request accepted",
        "tenant_id": str(tenant.id),
        "requested_by": str(current_user.id),
    }


__all__ = ["router"]
