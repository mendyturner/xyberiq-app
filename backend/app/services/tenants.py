"""Tenant domain service."""

from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Role, RoleKey, Tenant

DEFAULT_ROLE_NAMES: dict[RoleKey, str] = {
    RoleKey.ADMIN: "Administrator",
    RoleKey.MANAGER: "Manager",
    RoleKey.EMPLOYEE: "Employee",
    RoleKey.HR: "Human Resources",
    RoleKey.IT: "IT",
}


class TenantService:
    """Encapsulates tenant management logic."""

    @staticmethod
    def create_tenant(*, db: Session, name: str, slug: str, contact_email: str) -> Tenant:
        tenant = Tenant(name=name, slug=slug, contact_email=contact_email)
        db.add(tenant)
        db.flush()

        TenantService._ensure_default_roles(db=db, tenant_id=tenant.id)
        return tenant

    @staticmethod
    def _ensure_default_roles(*, db: Session, tenant_id: uuid.UUID) -> None:
        for role_key, display_name in DEFAULT_ROLE_NAMES.items():
            stmt = (
                select(Role)
                .where(Role.tenant_id == tenant_id, Role.key == role_key)
                .execution_options(tenant_aware=False)
            )
            if db.execute(stmt).scalar_one_or_none() is None:
                db.add(Role(tenant_id=tenant_id, key=role_key, name=display_name))

    @staticmethod
    def get_by_slug(*, db: Session, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug).execution_options(tenant_aware=False)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(*, db: Session, tenant_id: uuid.UUID) -> Tenant | None:
        return db.get(Tenant, tenant_id)

    @staticmethod
    def get_by_billing_customer_id(*, db: Session, customer_id: str) -> Tenant | None:
        stmt = (
            select(Tenant)
            .where(Tenant.billing_customer_id == customer_id)
            .execution_options(tenant_aware=False)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def attach_billing_profile(
        *,
        db: Session,
        tenant: Tenant,
        customer_id: str,
        provider: str,
        subscription_status: str | None = None,
        plan_code: str | None = None,
        trial_ends_at: datetime | None = None,
    ) -> Tenant:
        tenant.billing_customer_id = customer_id
        tenant.billing_provider = provider
        tenant.subscription_status = subscription_status
        tenant.plan_code = plan_code
        tenant.trial_ends_at = trial_ends_at
        db.add(tenant)
        return tenant

    @staticmethod
    def update_subscription_status(
        *,
        db: Session,
        tenant: Tenant,
        status: str,
        plan_code: str | None = None,
    ) -> Tenant:
        tenant.subscription_status = status
        if plan_code:
            tenant.plan_code = plan_code
        db.add(tenant)
        return tenant


__all__ = ["TenantService"]
