"""Billing integration service (Stripe/ACH)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.schemas import BillingCustomer


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

        return BillingCustomer(
            customer_id=customer_id,
            email=email,
            trial_ends_at=trial_end,
            payment_provider=provider,
        )

    def activate_subscription(
        self,
        *,
        customer_id: str,
        plan_code: str,
        payment_method_id: str | None = None,
    ) -> dict:
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

        return {"status": status, "plan_code": plan_code}

    @staticmethod
    def _compute_trial_end(trial_days: int | None) -> datetime | None:
        if trial_days is None or trial_days <= 0:
            return None
        now = datetime.now(tz=timezone.utc)
        return now + timedelta(days=trial_days)


__all__ = ["BillingService"]
