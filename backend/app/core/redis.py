"""Redis client factory."""

from __future__ import annotations

from typing import Final

from redis import Redis

from app.core.config import get_settings

_REDIS_CLIENT: Redis | None = None
_REDIS_DECODE_RESPONSES: Final[bool] = True


def get_redis_client() -> Redis:
    """Return a singleton Redis client instance."""

    global _REDIS_CLIENT  # noqa: PLW0603
    if _REDIS_CLIENT is None:
        settings = get_settings()
        _REDIS_CLIENT = Redis.from_url(settings.redis_url, decode_responses=_REDIS_DECODE_RESPONSES)
    return _REDIS_CLIENT


def reset_redis_client() -> None:
    """Close and discard the cached Redis client (useful for tests)."""

    global _REDIS_CLIENT  # noqa: PLW0603
    if _REDIS_CLIENT is not None:
        _REDIS_CLIENT.close()
        _REDIS_CLIENT = None


__all__ = ["get_redis_client", "reset_redis_client"]
