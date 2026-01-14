"""Stripe billing endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_settings_dependency
from app.core.config import Settings
from app.core.tenant import tenant_context
from app.schemas import (
    CheckoutSessionResponse,
    CreateCheckoutSessionRequest,
    CreatePortalSessionRequest,
    PortalSessionResponse,
    WebhookResponse,
)
from app.services.audit import AuditService
from app.services.billing import BillingService
from app.services.tenants import TenantService

router = APIRouter(prefix="/billing", tags=["Billing"])

logger = logging.getLogger(__name__)


@router.post("/checkout-session", response_model=CheckoutSessionResponse, status_code=status.HTTP_201_CREATED)
def create_checkout_session(
    payload: CreateCheckoutSessionRequest,
    settings: Settings = Depends(get_settings_dependency),
) -> CheckoutSessionResponse:
    billing_service = BillingService(settings)
    try:
        session = billing_service.create_checkout_session(lookup_key=payload.lookup_key, quantity=payload.quantity)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to create checkout session")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CheckoutSessionResponse(session_id=session["id"], url=session["url"])


@router.post("/portal-session", response_model=PortalSessionResponse, status_code=status.HTTP_201_CREATED)
def create_portal_session(
    payload: CreatePortalSessionRequest,
    settings: Settings = Depends(get_settings_dependency),
) -> PortalSessionResponse:
    billing_service = BillingService(settings)
    try:
        session = billing_service.create_billing_portal_session(
            checkout_session_id=payload.checkout_session_id,
            customer_id=payload.customer_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to create billing portal session")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PortalSessionResponse(url=session["url"])


@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    settings: Settings = Depends(get_settings_dependency),
    db: Session = Depends(get_db),
    stripe_signature: str | None = Header(default=None, convert_underscores=False, alias="Stripe-Signature"),
) -> WebhookResponse:
    payload = await request.body()
    billing_service = BillingService(settings)

    try:
        event = billing_service.construct_event(payload=payload, signature=stripe_signature)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Stripe webhook signature validation failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature") from exc

    def _get(obj: object, key: str, default: object = None) -> object:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    event_type = _get(event, "type")
    data_container = _get(event, "data", {})
    data_object = _get(data_container, "object", {})

    customer_id = _get(data_object, "customer")
    plan_id = _get(_get(data_object, "plan", {}), "id")
    status_value = _get(data_object, "status")
    trial_end = _get(data_object, "trial_end")
    event_id = _get(event, "id")

    if customer_id:
        tenant = TenantService.get_by_billing_customer_id(db=db, customer_id=customer_id)
    else:
        tenant = None

    if tenant:
        with tenant_context(tenant.id, tenant.slug):
            if event_type in {
                "customer.subscription.created",
                "customer.subscription.updated",
                "entitlements.active_entitlement_summary.updated",
            }:
                TenantService.update_subscription_status(
                    db=db,
                    tenant=tenant,
                    status=status_value or "active",
                    plan_code=plan_id,
                )
                AuditService.log(
                    db=db,
                    tenant_id=tenant.id,
                    actor_user_id=None,
                    action=f"billing.{event_type}",
                    meta={"status": status_value, "plan_id": plan_id, "event_id": event_id},
                )
                db.commit()
            elif event_type == "customer.subscription.deleted":
                TenantService.update_subscription_status(db=db, tenant=tenant, status="canceled")
                AuditService.log(
                    db=db,
                    tenant_id=tenant.id,
                    actor_user_id=None,
                    action="billing.subscription_canceled",
                    meta={"event_id": event_id},
                )
                db.commit()
            elif event_type == "customer.subscription.trial_will_end":
                AuditService.log(
                    db=db,
                    tenant_id=tenant.id,
                    actor_user_id=None,
                    action="billing.trial_will_end",
                    meta={"trial_end": trial_end, "event_id": event_id},
                )
                db.commit()
    else:
        logger.warning(
            "Received Stripe webhook for unknown customer",
            extra={"customer_id": customer_id, "event_type": event_type},
        )

    return WebhookResponse()


__all__ = ["router"]
