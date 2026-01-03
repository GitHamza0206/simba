"""Prometheus metrics service for latency tracking."""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Generator

from prometheus_client import Histogram, generate_latest, CONTENT_TYPE_LATEST

# Latency histograms with buckets optimized for sub-100ms targets
EMBEDDING_LATENCY = Histogram(
    "rag_embedding_latency_seconds",
    "Time spent generating query embeddings",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0),
)

SEARCH_LATENCY = Histogram(
    "rag_search_latency_seconds",
    "Time spent searching Qdrant",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0),
)

RERANK_LATENCY = Histogram(
    "rag_rerank_latency_seconds",
    "Time spent reranking results",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0),
)

RETRIEVAL_LATENCY = Histogram(
    "rag_retrieval_total_latency_seconds",
    "Total time for retrieval (embedding + search + optional rerank)",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0),
)


@contextmanager
def track_latency(histogram: Histogram) -> Generator[None, None, None]:
    """Context manager to track latency for a code block.

    Usage:
        with track_latency(EMBEDDING_LATENCY):
            embedding = get_embedding(query)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        histogram.observe(duration)


def track_embedding_latency(func: Callable) -> Callable:
    """Decorator to track embedding generation latency."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with track_latency(EMBEDDING_LATENCY):
            return func(*args, **kwargs)

    return wrapper


def track_search_latency(func: Callable) -> Callable:
    """Decorator to track search latency."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with track_latency(SEARCH_LATENCY):
            return func(*args, **kwargs)

    return wrapper


def track_rerank_latency(func: Callable) -> Callable:
    """Decorator to track reranking latency."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with track_latency(RERANK_LATENCY):
            return func(*args, **kwargs)

    return wrapper


def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
