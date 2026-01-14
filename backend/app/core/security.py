"""Security helpers for authentication and authorization."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import Settings


class InvalidTokenError(Exception):
    """Raised when a token cannot be decoded or validated."""


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a salted hash of the supplied password."""

    return _pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a stored hash."""

    try:
        return _pwd_context.verify(password, hashed_password)
    except ValueError:
        return False


def _build_claims(
    *,
    subject: uuid.UUID,
    tenant_id: uuid.UUID,
    scope: str,
    ttl: timedelta,
    settings: Settings,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "scope": scope,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": secrets.token_hex(16),
    }
    if extra:
        payload.update(extra)
    return payload


def encode_token(payload: dict[str, Any], *, settings: Settings) -> str:
    """Encode a JWT from the supplied payload."""

    return jwt.encode(payload, key=settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, settings: Settings) -> dict[str, Any]:
    """Decode a JWT returning its payload or raise ``InvalidTokenError``."""

    try:
        payload = jwt.decode(
            token,
            key=settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Invalid token") from exc
    return payload


def create_access_token(*, subject: uuid.UUID, tenant_id: uuid.UUID, settings: Settings) -> dict[str, Any]:
    """Produce JWT payload for access token."""

    ttl = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    return _build_claims(subject=subject, tenant_id=tenant_id, scope="access", ttl=ttl, settings=settings)


def create_refresh_token(
    *, subject: uuid.UUID, tenant_id: uuid.UUID, settings: Settings, extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Produce JWT payload for refresh token."""

    ttl = timedelta(minutes=settings.jwt_refresh_token_expires_minutes)
    return _build_claims(
        subject=subject,
        tenant_id=tenant_id,
        scope="refresh",
        ttl=ttl,
        settings=settings,
        extra=extra,
    )


def generate_reset_token() -> str:
    """Return secure random token for password reset or enrollment."""

    return secrets.token_urlsafe(32)


__all__ = [
    "InvalidTokenError",
    "hash_password",
    "verify_password",
    "encode_token",
    "decode_token",
    "create_access_token",
    "create_refresh_token",
    "generate_reset_token",
]
