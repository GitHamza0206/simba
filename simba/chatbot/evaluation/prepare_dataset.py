"""
Simple dataset preparation utilities for RAG evaluation.

This module provides functions to load and format datasets from CSV files
for evaluation with the RAG evaluation system.
"""

import json
import os
import pandas as pd
from typing import List, Dict, Any, Optional

class RAGEvaluationSample:
    """A single sample for RAG evaluation."""
    def __init__(self, question: str, contexts: List[str], answer: str, 
                 reference_answer: Optional[str] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.question = question
        self.contexts = contexts
        self.answer = answer
        self.reference_answer = reference_answer
        self.metadata = metadata or {}

class RAGEvaluationDataset:
    """A dataset for RAG evaluation."""
    
    def __init__(self, samples: List[RAGEvaluationSample] = None):
        self.samples = samples or []
    
    def add_sample(self, sample: RAGEvaluationSample):
        """Add a single sample to the dataset."""
        self.samples.append(sample)
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        return self.samples[idx]
    
    def save_to_json(self, filepath: str):
        """Save the dataset to a JSON file."""
        data = []
        for sample in self.samples:
            sample_dict = {
                "question": sample.question,
                "contexts": sample.contexts,
                "answer": sample.answer,
            }
            if sample.reference_answer:
                sample_dict["reference_answer"] = sample.reference_answer
            if sample.metadata:
                sample_dict["metadata"] = sample.metadata
            data.append(sample_dict)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Dataset saved to {filepath}")
    
    @classmethod
    def from_json(cls, filepath: str) -> 'RAGEvaluationDataset':
        """Load a dataset from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        samples = []
        for item in data:
            samples.append(RAGEvaluationSample(
                question=item["question"],
                contexts=item["contexts"],
                answer=item["answer"],
                reference_answer=item.get("reference_answer"),
                metadata=item.get("metadata")
            ))
        
        return cls(samples)

def load_from_csv(filepath: str, 
                 question_col: str, 
                 contexts_col: str = None, 
                 answer_col: str = None,
                 reference_answer_col: str = None,
                 contexts_separator: str = '|||') -> RAGEvaluationDataset:
    """
    Load a dataset from a CSV file.
    
    Args:
        filepath: Path to the CSV file
        question_col: Column name for questions
        contexts_col: Column name for contexts (optional)
        answer_col: Column name for answers (optional)
        reference_answer_col: Column name for reference answers (optional)
        contexts_separator: String separator for multiple contexts in a single cell
        
    Returns:
        A RAGEvaluationDataset
    """
    df = pd.read_csv(filepath)
    dataset = RAGEvaluationDataset()
    
    for _, row in df.iterrows():
        contexts = []
        if contexts_col and contexts_col in df.columns:
            contexts_str = row[contexts_col]
            # If contexts are stored as a single string with separators
            if isinstance(contexts_str, str):
                contexts = contexts_str.split(contexts_separator)
                contexts = [c.strip() for c in contexts]
        
        sample = RAGEvaluationSample(
            question=row[question_col],
            contexts=contexts,
            answer=row[answer_col] if answer_col and answer_col in df.columns else "",
            reference_answer=row[reference_answer_col] if reference_answer_col and reference_answer_col in df.columns else None,
            metadata={k: v for k, v in row.items() if k not in [question_col, contexts_col, answer_col, reference_answer_col]}
        )
        dataset.add_sample(sample)
    
    return dataset

