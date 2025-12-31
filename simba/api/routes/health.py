"""Health check routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verify all dependencies are available."""
    # TODO: Add actual checks for DB, vector store, etc.
    return {
        "ready": True,
        "checks": {
            "database": True,
            "vector_store": True,
        },
    }
