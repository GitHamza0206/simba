import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pathlib import Path

from simba.api.middleware.auth import get_current_user
from simba.models.user import UserResponse
from simba.core.config import Settings

logger = logging.getLogger(__name__)

# Create router
config_router = APIRouter(
    prefix="/config",
    tags=["configuration"]
)

# Global settings instance
settings = Settings.load_from_yaml()

@config_router.get(
    "",
    response_model=Dict[str, Any],
    summary="Get current configuration",
    description="Retrieve the complete application configuration"
)
async def get_config(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get the complete configuration"""
    try:
        return {
            "llm": settings.llm.model_dump(),
            "embedding": settings.embedding.model_dump(),
            "vector_store": settings.vector_store.model_dump(),
            "retrieval": settings.retrieval.model_dump(),
            "project": settings.project.model_dump(),
            "database": settings.database.model_dump(),
            "storage": settings.storage.model_dump(),
            "celery": settings.celery.model_dump()
        }
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        ) 