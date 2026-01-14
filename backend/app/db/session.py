"""Database engine and session management."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from app.core.config import get_settings
from app.core.tenant import current_tenant_id
from app.db.base import Base
from app.db.models.mixins import TenantScopedMixin

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return a singleton SQLAlchemy engine instance."""

    global _ENGINE  # noqa: PLW0603
    if _ENGINE is None:
        settings = get_settings()
        _ENGINE = create_engine(settings.database_url, echo=settings.database_echo, future=True)
    return _ENGINE


def _get_session_factory() -> sessionmaker[Session]:
    """Return configured session factory."""

    global _SESSION_FACTORY  # noqa: PLW0603
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _SESSION_FACTORY


def SessionLocal() -> Session:
    """Create a new session."""

    return _get_session_factory()()


def init_db() -> None:
    """Ensure metadata is created (primarily for development/testing)."""

    engine = get_engine()
    Base.metadata.create_all(bind=engine)


@event.listens_for(Session, "do_orm_execute")  # type: ignore[arg-type]
def _enforce_tenant_scope(orm_execute_state: Any) -> None:
    """Apply tenant criteria for SELECT statements automatically."""

    if (
        not orm_execute_state.is_select
        or orm_execute_state.execution_options.get("tenant_aware", True) is False
    ):
        return

    tenant_id = current_tenant_id()
    if tenant_id is None:
        return

    uuid_tenant_id = uuid.UUID(str(tenant_id))

    orm_execute_state.statement = orm_execute_state.statement.options(
        with_loader_criteria(TenantScopedMixin, lambda cls: cls.tenant_id == uuid_tenant_id, include_aliases=True)
    )


@event.listens_for(Session, "before_flush")  # type: ignore[arg-type]
def _inject_tenant_id(session: Session, flush_context: Any, instances: Any) -> None:
    """Set tenant_id for new tenant scoped instances automatically."""

    tenant_id = current_tenant_id()
    if tenant_id is None:
        return

    uuid_tenant_id = uuid.UUID(str(tenant_id))
    for instance in session.new:
        if hasattr(instance, "tenant_id") and getattr(instance, "tenant_id") is None:
            setattr(instance, "tenant_id", uuid_tenant_id)


__all__ = ["SessionLocal", "get_engine", "init_db"]
