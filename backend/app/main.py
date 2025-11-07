"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import auth as auth_routes
from app.api.routes import admin as admin_routes
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="XyberIQ Training Portal",
        version="0.1.0",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    app.include_router(auth_routes.router, prefix=settings.api_v1_prefix)
    app.include_router(admin_routes.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()


__all__ = ["app", "create_app"]
