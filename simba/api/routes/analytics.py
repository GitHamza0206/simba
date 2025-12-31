"""Analytics routes."""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/analytics")


# --- Schemas ---


class MetricValue(BaseModel):
    value: float
    change: float  # percentage change
    period: str


class OverviewResponse(BaseModel):
    total_conversations: MetricValue
    total_messages: MetricValue
    avg_response_time_ms: MetricValue
    resolution_rate: MetricValue
    user_satisfaction: MetricValue


class EvalMetrics(BaseModel):
    relevance_score: float
    accuracy_score: float
    completeness_score: float
    citation_score: float


class DailyStats(BaseModel):
    date: str
    conversations: int
    messages: int
    avg_response_time_ms: int


# --- Routes ---


@router.get("/overview", response_model=OverviewResponse)
async def get_overview():
    """Get analytics overview."""
    # TODO: Implement actual analytics from DB
    return OverviewResponse(
        total_conversations=MetricValue(value=0, change=0, period="week"),
        total_messages=MetricValue(value=0, change=0, period="week"),
        avg_response_time_ms=MetricValue(value=0, change=0, period="week"),
        resolution_rate=MetricValue(value=0, change=0, period="week"),
        user_satisfaction=MetricValue(value=0, change=0, period="week"),
    )


@router.get("/evals", response_model=EvalMetrics)
async def get_eval_metrics():
    """Get AI evaluation metrics."""
    # TODO: Implement actual eval metrics
    return EvalMetrics(
        relevance_score=0.0,
        accuracy_score=0.0,
        completeness_score=0.0,
        citation_score=0.0,
    )


@router.get("/daily", response_model=list[DailyStats])
async def get_daily_stats(days: int = 7):
    """Get daily statistics."""
    # TODO: Implement actual daily stats
    return []
