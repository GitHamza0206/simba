"""Prometheus metrics endpoint."""

from fastapi import APIRouter
from fastapi.responses import Response

from simba.services.metrics_service import get_metrics, get_metrics_content_type

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """Expose Prometheus metrics for scraping."""
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type(),
    )
