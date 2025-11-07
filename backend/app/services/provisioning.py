"""Customer provisioning orchestration."""

from __future__ import annotations

import json
import logging

from app.core.config import Settings
from app.schemas import TenantProvisioningRequest

logger = logging.getLogger(__name__)


class ProvisioningService:
    """Publishes provisioning events to downstream systems."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._sns = self._configure_sns(settings=settings)

    @staticmethod
    def _configure_sns(*, settings: Settings):
        if not settings.provisioning_topic_arn:
            return None
        try:
            import boto3  # type: ignore
        except ImportError:
            logger.warning("boto3 not installed, provisioning events will not be published")
            return None
        return boto3.client("sns")

    def publish(self, payload: TenantProvisioningRequest) -> None:
        message = json.dumps(payload.dict())
        if self._sns:
            self._sns.publish(TopicArn=self.settings.provisioning_topic_arn, Message=message)
            logger.info(
                "Published provisioning event",
                extra={"tenant_id": str(payload.tenant_id), "customer_id": payload.customer_id},
            )
        else:
            logger.info(
                "Provisioning event (no SNS configured)",
                extra={"tenant_id": str(payload.tenant_id), "customer_id": payload.customer_id, "message": message},
            )


__all__ = ["ProvisioningService"]
