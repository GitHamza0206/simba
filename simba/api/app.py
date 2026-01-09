"""FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from simba.api.routes import (
    analytics,
    collections,
    conversations,
    documents,
    evals,
    health,
    metrics,
)
from simba.core.config import settings
from simba.models import init_db
from simba.services.chat_service import shutdown_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    yield
    # Shutdown
    await shutdown_checkpointer()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Customer Service Assistant - AI-powered support",
        version=settings.app_version,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Conversation-Id"],
    )

    # Routes
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(metrics.router, prefix=settings.api_prefix, tags=["metrics"])
    app.include_router(collections.router, prefix=settings.api_prefix, tags=["collections"])
    app.include_router(documents.router, prefix=settings.api_prefix, tags=["documents"])
    app.include_router(conversations.router, prefix=settings.api_prefix, tags=["conversations"])
    app.include_router(analytics.router, prefix=settings.api_prefix, tags=["analytics"])
    app.include_router(evals.router, prefix=settings.api_prefix, tags=["evals"])

    # Global exception handler to ensure CORS headers on error responses
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    return app


app = create_app()
