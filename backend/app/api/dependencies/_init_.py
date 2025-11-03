"""Common dependency overrides for FastAPI routes."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request lifespan."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_settings_dependency() -> Settings:
    """Expose application settings inside request scope."""

    return get_settings()


SettingsDep = Depends(get_settings_dependency)


__all__ = ["get_db", "get_settings_dependency", "SettingsDep"]
