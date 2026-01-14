"""ORM mixins used across models."""

from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Mixin adding a UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """Mixin providing created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Mixin providing soft delete timestamp."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TenantScopedMixin:
    """Mixin that injects tenant_id and marks the model as tenant scoped."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)


__all__ = ["UUIDPrimaryKeyMixin", "TimestampMixin", "SoftDeleteMixin", "TenantScopedMixin"]
