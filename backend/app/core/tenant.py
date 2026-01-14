"""Tenant context management utilities."""

from __future__ import annotations

import contextlib
import contextvars
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


_tenant_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_id", default=None)
_tenant_slug_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_slug", default=None)


@dataclass
class TenantToken:
    """Represents a context var token pair for resetting tenant scope."""

    tenant_id_token: contextvars.Token[str | None]
    tenant_slug_token: contextvars.Token[str | None]


def set_current_tenant(tenant_id: Any, tenant_slug: str | None = None) -> TenantToken:
    """Assign the tenant context for the current async/task execution."""

    tenant_id_token = _tenant_id_ctx.set(str(tenant_id))
    tenant_slug_token = _tenant_slug_ctx.set(tenant_slug)
    return TenantToken(tenant_id_token=tenant_id_token, tenant_slug_token=tenant_slug_token)


def reset_current_tenant(token: TenantToken) -> None:
    """Reset tenant context to the previous value."""

    _tenant_id_ctx.reset(token.tenant_id_token)
    _tenant_slug_ctx.reset(token.tenant_slug_token)


def current_tenant_id() -> str | None:
    """Return the tenant identifier currently bound to the context."""

    return _tenant_id_ctx.get()


def current_tenant_slug() -> str | None:
    """Return the tenant slug currently bound to the context."""

    return _tenant_slug_ctx.get()


@contextlib.contextmanager
def tenant_context(tenant_id: Any, tenant_slug: str | None = None) -> Iterator[None]:
    """Context manager that temporarily binds tenant information."""

    token = set_current_tenant(tenant_id=tenant_id, tenant_slug=tenant_slug)
    try:
        yield
    finally:
        reset_current_tenant(token)


__all__ = [
    "TenantToken",
    "set_current_tenant",
    "reset_current_tenant",
    "current_tenant_id",
    "current_tenant_slug",
    "tenant_context",
]
