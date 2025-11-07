"""Application configuration management."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import BaseSettings, Field, PostgresDsn, RedisDsn, validator


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    environment: str = Field(default="development", env="APP_ENV")
    api_v1_prefix: str = Field(default="/api")
    secret_key: str = Field(default="changeme", env="APP_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expires_minutes: int = Field(default=15)
    jwt_refresh_token_expires_minutes: int = Field(default=60 * 24 * 30)
    jwt_issuer: str = Field(default="xyberiq-app")
    jwt_audience: str = Field(default="xyberiq-clients")

    database_url: PostgresDsn = Field(
        default="postgresql+psycopg2://xyberiq:xyberiq@localhost:5432/xyberiq",
        env="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")

    redis_url: RedisDsn = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    stripe_api_key: str | None = Field(default=None, env="STRIPE_API_KEY")
    stripe_publishable_key: str | None = Field(default=None, env="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: str | None = Field(default=None, env="STRIPE_WEBHOOK_SECRET")
    ach_provider_api_url: str | None = Field(default=None, env="ACH_API_URL")
    ach_provider_api_key: str | None = Field(default=None, env="ACH_API_KEY")
    billing_free_trial_days: int = Field(default=7)
    billing_success_url: str = Field(default="http://localhost:4242/success.html")
    billing_cancel_url: str = Field(default="http://localhost:4242/cancel.html")
    billing_portal_return_url: str = Field(default="http://localhost:4242")

    provisioning_topic_arn: str | None = Field(default=None, env="PROVISIONING_TOPIC_ARN")
    default_from_email: str = Field(default="support@xyberiq.io")

    oidc_enabled: bool = Field(default=False, env="OIDC_ENABLED")
    oidc_providers: list[str] = Field(default_factory=list)

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("oidc_providers", pre=True)
    def _split_providers(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [provider.strip() for provider in value.split(",") if provider.strip()]
        if value is None:
            return []
        return list(value)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


__all__ = ["Settings", "get_settings"]
