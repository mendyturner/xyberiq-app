"""Authentication service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from redis import Redis

from app.core.config import Settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    encode_token,
    generate_reset_token,
)
from app.db.models import Tenant, User


REFRESH_TOKEN_PREFIX = "refresh:"
PASSWORD_RESET_PREFIX = "pwdreset:"
PASSWORD_RESET_TTL_SECONDS = 3600


@dataclass
class TokenPair:
    """Container for issued tokens."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class AuthService:
    """Token issuance, validation, and password reset helpers."""

    @staticmethod
    def issue_token_pair(*, user: User, tenant: Tenant, settings: Settings, redis: Redis) -> TokenPair:
        roles = [user_role.role.key.value for user_role in user.roles if user_role.role is not None]
        access_payload = create_access_token(subject=user.id, tenant_id=tenant.id, settings=settings)
        access_payload["roles"] = roles

        refresh_payload = create_refresh_token(
            subject=user.id,
            tenant_id=tenant.id,
            settings=settings,
            extra={"roles": roles},
        )

        access_token = encode_token(access_payload, settings=settings)
        refresh_token = encode_token(refresh_payload, settings=settings)

        expires_in = settings.jwt_access_token_expires_minutes * 60
        refresh_ttl = settings.jwt_refresh_token_expires_minutes * 60

        redis.setex(f"{REFRESH_TOKEN_PREFIX}{refresh_payload['jti']}", refresh_ttl, str(user.id))

        return TokenPair(access_token=access_token, refresh_token=refresh_token, expires_in=expires_in)

    @staticmethod
    def validate_refresh_token(*, token: str, settings: Settings, redis: Redis) -> dict:
        payload = decode_token(token, settings=settings)
        if payload.get("scope") != "refresh":
            raise InvalidTokenError("Invalid refresh token scope")
        key = f"{REFRESH_TOKEN_PREFIX}{payload.get('jti')}"
        if not redis.exists(key):
            raise InvalidTokenError("Refresh token has been revoked")
        return payload

    @staticmethod
    def revoke_refresh_token(*, redis: Redis, jti: str) -> None:
        if not jti:
            return
        redis.delete(f"{REFRESH_TOKEN_PREFIX}{jti}")

    @staticmethod
    def create_password_reset_token(
        *,
        redis: Redis,
        settings: Settings,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        token = generate_reset_token()
        key = f"{PASSWORD_RESET_PREFIX}{token}"
        redis.setex(key, PASSWORD_RESET_TTL_SECONDS, f"{tenant_id}:{user_id}")
        return token

    @staticmethod
    def consume_password_reset_token(*, redis: Redis, token: str) -> tuple[uuid.UUID, uuid.UUID] | None:
        key = f"{PASSWORD_RESET_PREFIX}{token}"
        data = redis.get(key)
        if data is None:
            return None
        redis.delete(key)
        tenant_id_str, user_id_str = data.split(":")
        return uuid.UUID(tenant_id_str), uuid.UUID(user_id_str)


__all__ = ["AuthService", "TokenPair"]
