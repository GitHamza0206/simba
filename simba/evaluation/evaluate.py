"""RAG accuracy evaluation script.

Usage:
    uv run python -m simba.evaluation.evaluate --test-file test_queries.json --collection default
"""

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

from simba.services import retrieval_service


@dataclass
class EvaluationResult:
    """Results from a single query evaluation."""

    query: str
    expected_doc_ids: list[str]
    retrieved_doc_ids: list[str]
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    latency_ms: float


def recall_at_k(expected: list[str], retrieved: list[str]) -> float:
    """Calculate Recall@K - proportion of relevant docs retrieved."""
    if not expected:
        return 1.0
    retrieved_set = set(retrieved)
    hits = sum(1 for doc_id in expected if doc_id in retrieved_set)
    return hits / len(expected)


def precision_at_k(expected: list[str], retrieved: list[str]) -> float:
    """Calculate Precision@K - proportion of retrieved docs that are relevant."""
    if not retrieved:
        return 0.0
    expected_set = set(expected)
    hits = sum(1 for doc_id in retrieved if doc_id in expected_set)
    return hits / len(retrieved)


def reciprocal_rank(expected: list[str], retrieved: list[str]) -> float:
    """Calculate Reciprocal Rank - 1/position of first relevant doc."""
    expected_set = set(expected)
    for i, doc_id in enumerate(retrieved, 1):
        if doc_id in expected_set:
            return 1.0 / i
    return 0.0


def evaluate_query(
    query: str,
    expected_doc_ids: list[str],
    collection_name: str,
    limit: int = 5,
    rerank: bool = False,
) -> EvaluationResult:
    """Evaluate a single query."""
    start = time.perf_counter()

    chunks = retrieval_service.retrieve(
        query=query,
        collection_name=collection_name,
        limit=limit,
        rerank=rerank,
    )

    latency_ms = (time.perf_counter() - start) * 1000

    retrieved_doc_ids = [chunk.document_id for chunk in chunks]

    return EvaluationResult(
        query=query,
        expected_doc_ids=expected_doc_ids,
        retrieved_doc_ids=retrieved_doc_ids,
        recall_at_k=recall_at_k(expected_doc_ids, retrieved_doc_ids),
        precision_at_k=precision_at_k(expected_doc_ids, retrieved_doc_ids),
        reciprocal_rank=reciprocal_rank(expected_doc_ids, retrieved_doc_ids),
        latency_ms=latency_ms,
    )


def run_evaluation(
    test_file: Path,
    collection_name: str,
    limit: int = 5,
    rerank: bool = False,
) -> dict:
    """Run evaluation on a test file.

    Test file format (JSON):
    [
        {
            "query": "What is the return policy?",
            "expected_doc_ids": ["doc_123", "doc_456"]
        },
        ...
    ]
    """
    with open(test_file) as f:
        test_data = json.load(f)

    results: list[EvaluationResult] = []

    for item in test_data:
        result = evaluate_query(
            query=item["query"],
            expected_doc_ids=item["expected_doc_ids"],
            collection_name=collection_name,
            limit=limit,
            rerank=rerank,
        )
        results.append(result)

    # Aggregate metrics
    n = len(results)
    avg_recall = sum(r.recall_at_k for r in results) / n if n else 0
    avg_precision = sum(r.precision_at_k for r in results) / n if n else 0
    avg_mrr = sum(r.reciprocal_rank for r in results) / n if n else 0
    avg_latency = sum(r.latency_ms for r in results) / n if n else 0
    p50_latency = sorted(r.latency_ms for r in results)[n // 2] if n else 0
    p99_latency = sorted(r.latency_ms for r in results)[int(n * 0.99)] if n else 0

    return {
        "num_queries": n,
        "metrics": {
            "recall@k": round(avg_recall, 4),
            "precision@k": round(avg_precision, 4),
            "mrr": round(avg_mrr, 4),
        },
        "latency": {
            "avg_ms": round(avg_latency, 2),
            "p50_ms": round(p50_latency, 2),
            "p99_ms": round(p99_latency, 2),
        },
        "config": {
            "collection": collection_name,
            "limit": limit,
            "rerank": rerank,
        },
        "per_query": [
            {
                "query": r.query,
                "recall": round(r.recall_at_k, 4),
                "precision": round(r.precision_at_k, 4),
                "rr": round(r.reciprocal_rank, 4),
                "latency_ms": round(r.latency_ms, 2),
            }
            for r in results
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval accuracy")
    parser.add_argument(
        "--test-file",
        type=Path,
        required=True,
        help="Path to test queries JSON file",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="default",
        help="Collection name to search",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of results to retrieve",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Enable cross-encoder reranking",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for results (JSON)",
    )

    args = parser.parse_args()

    print(f"Running evaluation on {args.test_file}")
    print(f"Collection: {args.collection}, Limit: {args.limit}, Rerank: {args.rerank}")
    print("-" * 50)

    results = run_evaluation(
        test_file=args.test_file,
        collection_name=args.collection,
        limit=args.limit,
        rerank=args.rerank,
    )

    print(f"\nResults ({results['num_queries']} queries):")
    print(f"  Recall@{args.limit}:    {results['metrics']['recall@k']:.2%}")
    print(f"  Precision@{args.limit}: {results['metrics']['precision@k']:.2%}")
    print(f"  MRR:          {results['metrics']['mrr']:.4f}")
    print(f"\nLatency:")
    print(f"  Avg:  {results['latency']['avg_ms']:.1f}ms")
    print(f"  P50:  {results['latency']['p50_ms']:.1f}ms")
    print(f"  P99:  {results['latency']['p99_ms']:.1f}ms")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nFull results saved to {args.output}")


if __name__ == "__main__":
    main()
