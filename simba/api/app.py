"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simba.core.config import settings
from simba.api.routes import conversations, documents, analytics, health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Customer Service Assistant - AI-powered support",
        version=settings.app_version,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(documents.router, prefix=settings.api_prefix, tags=["documents"])
    app.include_router(conversations.router, prefix=settings.api_prefix, tags=["conversations"])
    app.include_router(analytics.router, prefix=settings.api_prefix, tags=["analytics"])

    return app


app = create_app()
