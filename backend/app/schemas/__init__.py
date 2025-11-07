"""Pydantic schemas for API contracts."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, constr

from app.db.models.enums import RoleKey, UserStatus


class TenantAdmin(BaseModel):
    """Administrator account details for new tenants."""

    email: EmailStr
    password: constr(min_length=12)
    first_name: constr(min_length=1, max_length=255)
    last_name: constr(min_length=1, max_length=255)


class RegisterTenantRequest(BaseModel):
    """Request body for tenant registration."""

    tenant_name: constr(min_length=2, max_length=255)
    tenant_slug: constr(min_length=2, max_length=255)
    contact_email: EmailStr
    plan_code: constr(min_length=2, max_length=64) = Field(default="standard")
    admin: TenantAdmin


class TokenResponse(BaseModel):
    """OAuth-style token payload."""

    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(description="Seconds until access token expiration")


class LoginRequest(BaseModel):
    """Tenant login credentials."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Refresh token rotation request."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Password reset initiation request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Password reset completion request."""

    token: str
    new_password: constr(min_length=12)


class MeResponse(BaseModel):
    """Profile information for the authenticated user."""

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    department: str | None = None
    title: str | None = None
    status: UserStatus
    roles: list[RoleKey]


class TenantProvisioningRequest(BaseModel):
    """Internal event payload for provisioning automation."""

    tenant_id: uuid.UUID
    customer_id: str
    plan_code: str
    trial_ends_at: datetime | None = None
    metadata: dict[str, str | int | float | bool] | None = None


class BillingCustomer(BaseModel):
    """Billing customer representation returned by the billing service."""

    customer_id: str
    email: EmailStr
    trial_ends_at: datetime | None = None
    payment_provider: str


class UserOut(BaseModel):
    """Lightweight user representation for dashboards."""

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    status: UserStatus
    roles: list[RoleKey] = Field(default_factory=list)


__all__ = [
    "TenantAdmin",
    "RegisterTenantRequest",
    "TokenResponse",
    "LoginRequest",
    "RefreshRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "MeResponse",
    "TenantProvisioningRequest",
    "BillingCustomer",
    "UserOut",
]
