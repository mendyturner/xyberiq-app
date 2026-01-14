"""Authentication API routes."""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_db, get_settings_dependency
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.tenant import get_current_tenant
from app.core.config import Settings
from app.core.redis import get_redis_client
from app.core.security import InvalidTokenError, decode_token
from app.core.tenant import tenant_context
from app.db.models import RoleKey, Tenant, User, UserRole
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterTenantRequest,
    ResetPasswordRequest,
    TokenResponse,
    TenantProvisioningRequest,
)
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.billing import BillingService
from app.services.provisioning import ProvisioningService
from app.services.tenants import TenantService
from app.services.users import UserService


router = APIRouter(prefix="/auth", tags=["Auth"])


def _redis_client() -> Redis:
    return get_redis_client()


def _enforce_rate_limit(redis: Redis, prefix: str, identifier: str, *, limit: int, window_seconds: int) -> None:
    key = f"ratelimit:{prefix}:{identifier}"
    current = redis.incr(key)
    if current == 1:
        redis.expire(key, window_seconds)
    if current > limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


@router.post("/register-tenant", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_tenant(
    payload: RegisterTenantRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    redis: Redis = Depends(_redis_client),
) -> TokenResponse:
    _enforce_rate_limit(
        redis=redis,
        prefix="register-tenant",
        identifier=request.client.host if request.client else "anonymous",
        limit=5,
        window_seconds=3600,
    )
    slug = re.sub(r"[^a-z0-9-]", "-", payload.tenant_slug.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant slug")
    if TenantService.get_by_slug(db=db, slug=slug) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already exists")

    billing_service = BillingService(settings)
    provisioning_service = ProvisioningService(settings)

    tenant = TenantService.create_tenant(
        db=db,
        name=payload.tenant_name,
        slug=slug,
        contact_email=payload.contact_email,
    )

    billing_customer = billing_service.create_customer(
        email=payload.contact_email,
        name=payload.tenant_name,
        trial_days=settings.billing_free_trial_days,
    )

    TenantService.attach_billing_profile(
        db=db,
        tenant=tenant,
        customer_id=billing_customer.customer_id,
        provider=billing_customer.payment_provider,
        subscription_status="trialing",
        plan_code=payload.plan_code,
        trial_ends_at=billing_customer.trial_ends_at,
    )

    admin_user = UserService.create_user(
        db=db,
        tenant_id=tenant.id,
        email=payload.admin.email,
        password=payload.admin.password,
        first_name=payload.admin.first_name,
        last_name=payload.admin.last_name,
        roles=[RoleKey.ADMIN, RoleKey.EMPLOYEE],
    )

    db.commit()
    db.refresh(tenant)

    provisioning_service.publish(
        TenantProvisioningRequest(
            tenant_id=tenant.id,
            customer_id=billing_customer.customer_id,
            plan_code=payload.plan_code,
            trial_ends_at=billing_customer.trial_ends_at,
            metadata={
                "tenant_slug": tenant.slug,
                "source_ip": request.client.host if request.client else "unknown",
            },
        )
    )

    with tenant_context(tenant.id, tenant.slug):
        admin_user = (
            db.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(UserRole.role))
                .where(User.id == admin_user.id)
            ).scalar_one()
        )
        token_pair = AuthService.issue_token_pair(user=admin_user, tenant=tenant, settings=settings, redis=redis)
        AuditService.log(
            db=db,
            tenant_id=tenant.id,
            actor_user_id=admin_user.id,
            action="tenant.register",
            meta={"tenant_slug": tenant.slug},
        )
        db.commit()

    return TokenResponse(**token_pair.__dict__)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    redis: Redis = Depends(_redis_client),
) -> TokenResponse:
    identifier = f"{tenant.id}:{payload.email.lower()}"
    _enforce_rate_limit(
        redis=redis,
        prefix="login",
        identifier=identifier,
        limit=settings.rate_limit_auth_per_minute,
        window_seconds=60,
    )
    with tenant_context(tenant.id, tenant.slug):
        user = UserService.authenticate(
            db=db,
            tenant_id=tenant.id,
            email=payload.email,
            password=payload.password,
        )
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token_pair = AuthService.issue_token_pair(user=user, tenant=tenant, settings=settings, redis=redis)
        AuditService.log(
            db=db,
            tenant_id=tenant.id,
            actor_user_id=user.id,
            action="auth.login",
        )
        db.commit()

    return TokenResponse(**token_pair.__dict__)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    redis: Redis = Depends(_redis_client),
) -> TokenResponse:
    try:
        refresh_payload = AuthService.validate_refresh_token(
            token=payload.refresh_token, settings=settings, redis=redis
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    tenant_id = uuid.UUID(refresh_payload["tenant_id"])
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    user = (
        db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.id == uuid.UUID(refresh_payload["sub"]))
        ).scalar_one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    AuthService.revoke_refresh_token(redis=redis, jti=refresh_payload["jti"])

    with tenant_context(tenant.id, tenant.slug):
        token_pair = AuthService.issue_token_pair(user=user, tenant=tenant, settings=settings, redis=redis)
        AuditService.log(
            db=db,
            tenant_id=tenant.id,
            actor_user_id=user.id,
            action="auth.refresh",
        )
        db.commit()

    return TokenResponse(**token_pair.__dict__)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    redis: Redis = Depends(_redis_client),
    tenant: Tenant = Depends(get_current_tenant),
) -> None:
    try:
        refresh_payload = AuthService.validate_refresh_token(
            token=payload.refresh_token, settings=settings, redis=redis
        )
    except InvalidTokenError:
        return None

    if str(refresh_payload.get("tenant_id")) != str(tenant.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")

    AuthService.revoke_refresh_token(redis=redis, jti=refresh_payload.get("jti", ""))

    user_id = refresh_payload.get("sub")
    if user_id:
        AuditService.log(
            db=db,
            tenant_id=tenant.id,
            actor_user_id=uuid.UUID(user_id),
            action="auth.logout",
        )
        db.commit()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    payload: ForgotPasswordRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    redis: Redis = Depends(_redis_client),
) -> None:
    identifier = f"{tenant.id}:{payload.email.lower()}"
    _enforce_rate_limit(redis=redis, prefix="forgot", identifier=identifier, limit=5, window_seconds=900)
    stmt = (
        select(User)
        .where(User.email == payload.email.lower(), User.tenant_id == tenant.id)
        .execution_options(tenant_aware=False)
    )
    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        return None

    token = AuthService.create_password_reset_token(
        redis=redis, settings=settings, tenant_id=tenant.id, user_id=user.id
    )
    AuditService.log(
        db=db,
        tenant_id=tenant.id,
        actor_user_id=user.id,
        action="auth.forgot_password",
        meta={"reset_token": token},
    )
    db.commit()


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(_redis_client),
) -> None:
    token_data = AuthService.consume_password_reset_token(redis=redis, token=payload.token)
    if token_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    tenant_id, user_id = token_data
    tenant = db.get(Tenant, tenant_id)
    user = db.get(User, user_id)
    if tenant is None or user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reset target not found")

    with tenant_context(tenant.id, tenant.slug):
        UserService.set_password(db=db, user=user, password=payload.new_password)
        AuditService.log(
            db=db,
            tenant_id=tenant.id,
            actor_user_id=user.id,
            action="auth.reset_password",
        )
        db.commit()


@router.get("/me", response_model=MeResponse)
def read_me(current_user: User = Depends(get_current_user)) -> MeResponse:
    roles = [user_role.role.key for user_role in current_user.roles if user_role.role is not None]
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        department=current_user.department,
        title=current_user.title,
        status=current_user.status,
        roles=roles,
    )


@router.get("/oidc/providers")
def list_oidc_providers(settings = Depends(get_settings_dependency)) -> dict[str, list[str]]:
    if not settings.oidc_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OIDC disabled")
    return {"providers": settings.oidc_providers}


@router.post("/oidc/{provider}/start", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def start_oidc_flow(provider: str, settings = Depends(get_settings_dependency)) -> None:
    if not settings.oidc_enabled or provider not in settings.oidc_providers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider unavailable")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC flow not implemented")
