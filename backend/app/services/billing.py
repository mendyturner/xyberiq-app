"""Billing integration service (Stripe/ACH)."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings
from app.schemas import BillingCustomer

logger = logging.getLogger(__name__)


class BillingService:
    """Facade for interacting with external billing providers."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._stripe = self._configure_stripe(settings=settings)

    @staticmethod
    def _configure_stripe(*, settings: Settings):
        if not settings.stripe_api_key:
            return None
        try:
            import stripe
        except ImportError:
            logger.warning("Stripe SDK not installed; falling back to stub billing implementation")
            return None
        stripe.api_key = settings.stripe_api_key
        return stripe

    def create_customer(self, *, email: str, name: str, trial_days: int | None = None) -> BillingCustomer:
        """Create a billing customer record."""

        trial_end = self._compute_trial_end(trial_days or self.settings.billing_free_trial_days)

        if self._stripe:
            customer = self._stripe.Customer.create(
                email=email,
                name=name,
                metadata={"source": "xyberiq-app"},
                trial_end=int(trial_end.timestamp()) if trial_end else None,
            )
            customer_id = customer["id"]
            provider = "stripe"
        else:
            customer_id = f"stub_{uuid.uuid4().hex[:12]}"
            provider = "stub"
            logger.info("Stub billing customer created", extra={"customer_id": customer_id})

        return BillingCustomer(
            customer_id=customer_id,
            email=email,
            trial_ends_at=trial_end,
            payment_provider=provider,
        )

    def create_checkout_session(self, *, lookup_key: str, quantity: int = 1) -> dict[str, str]:
        """Create a Stripe Checkout session for subscriptions."""

        if self._stripe:
            prices = self._stripe.Price.list(lookup_keys=[lookup_key], expand=["data.product"])
            if not prices.data:
                raise ValueError(f"No Stripe price configured for lookup key '{lookup_key}'")
            price_id = prices.data[0].id
            session = self._stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": quantity}],
                success_url=f"{self.settings.billing_success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=self.settings.billing_cancel_url,
                subscription_data={"trial_period_days": self.settings.billing_free_trial_days},
            )
            return {"id": session["id"], "url": session["url"]}

        session_id = f"stub_session_{uuid.uuid4().hex[:10]}"
        success_url = f"{self.settings.billing_success_url}?session_id={session_id}"
        logger.info(
            "Stub checkout session created",
            extra={"session_id": session_id, "lookup_key": lookup_key},
        )
        return {"id": session_id, "url": success_url}

    def create_billing_portal_session(
        self, *, checkout_session_id: str | None = None, customer_id: str | None = None
    ) -> dict[str, str]:
        """Create a Stripe Billing Portal session for customer self-service."""

        if self._stripe:
            resolved_customer_id = customer_id
            if not resolved_customer_id and checkout_session_id:
                checkout_session = self._stripe.checkout.Session.retrieve(checkout_session_id)
                resolved_customer_id = checkout_session.customer
            if not resolved_customer_id:
                raise ValueError("customer_id or checkout_session_id must be provided")

            portal_session = self._stripe.billing_portal.Session.create(
                customer=resolved_customer_id,
                return_url=self.settings.billing_portal_return_url,
            )
            return {"url": portal_session["url"]}

        logger.info(
            "Stub billing portal session requested",
            extra={"checkout_session_id": checkout_session_id, "customer_id": customer_id},
        )
        return {"url": self.settings.billing_portal_return_url}

    def construct_event(self, *, payload: bytes, signature: str | None) -> Any:
        """Validate and parse incoming Stripe webhook payloads."""

        if self._stripe and self.settings.stripe_webhook_secret and signature:
            return self._stripe.Webhook.construct_event(
                payload.decode("utf-8"),
                signature,
                self.settings.stripe_webhook_secret,
            )

        data = json.loads(payload.decode("utf-8"))
        if self._stripe:
            return self._stripe.Event.construct_from(data)
        logger.info("Stub webhook event received", extra={"event_type": data.get("type")})
        return data

    def activate_subscription(
        self,
        *,
        customer_id: str,
        plan_code: str,
        payment_method_id: str | None = None,
    ) -> dict[str, str]:
        """Start or update a subscription for the customer."""

        if self._stripe:
            subscription = self._stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": plan_code}],
                default_payment_method=payment_method_id,
                proration_behavior="create_prorations",
            )
            status = subscription["status"]
        else:
            status = "active"
            logger.info(
                "Stub subscription activation",
                extra={"customer_id": customer_id, "plan_code": plan_code},
            )

        return {"status": status, "plan_code": plan_code}

    @staticmethod
    def _compute_trial_end(trial_days: int | None) -> datetime | None:
        if trial_days is None or trial_days <= 0:
            return None
        now = datetime.now(tz=timezone.utc)
        return now + timedelta(days=trial_days)


__all__ = ["BillingService"]
