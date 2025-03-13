"""
Simba RAG Evaluation System

This module provides tools for evaluating RAG systems using RAGAS metrics.
"""

# Import key functions and classes for easier access
from simba.chatbot.evaluation.evaluate import evaluate_rag_response, score_with_ragas
from simba.chatbot.evaluation.prepare_dataset import (
    RAGEvaluationSample, 
    RAGEvaluationDataset,
    load_from_csv
)
from simba.chatbot.evaluation.evaluation_config import get_langfuse_client, get_ragas_metrics

# Define what's available when using "from simba.chatbot.evaluation import *"
__all__ = [
    'evaluate_rag_response',
    'score_with_ragas',
    'RAGEvaluationSample',
    'RAGEvaluationDataset',
    'load_from_csv',
    'prepare_synthetic_dataset',
    'run_evaluation_on_dataset',
    'generate_report',
    'get_langfuse_client',
    'get_ragas_metrics'
]

# This file makes the evaluation directory a Python package 