#!/usr/bin/env python
"""
Comprehensive test script to demonstrate the full functionality of the RetrieveManager in the Simba SDK.
This script shows how to:
1. Retrieve available retrieval strategies
2. Perform basic retrieval
3. Use different retrieval methods
4. Apply filters and scoring thresholds
5. Handle errors
"""

import sys
import json
from simba_sdk import SimbaClient

# Initialize the client with the correct URL
API_URL = "http://localhost:8000"  # Use your Simba API URL

def main():
    """Main function to demonstrate RetrieveManager functionality."""
    # Print header
    print("\n" + "="*80)
    print("Simba SDK - RetrieveManager Demo".center(80))
    print("="*80 + "\n")
    
    # Initialize the client
    print("Initializing Simba Client with API URL:", API_URL)
    client = SimbaClient(API_URL)
    
    # Get available retrieval strategies
    print("\n1. RETRIEVING AVAILABLE STRATEGIES")
    print("-" * 40)
    try:
        strategies = client.retriever.get_retrieval_strategies()
        print("Available retrieval strategies:")
        for strategy, description in strategies.get("strategies", {}).items():
            print(f"  - {strategy}: {description}")
    except Exception as e:
        print(f"Error getting retrieval strategies: {e}")
        print(f"Error type: {type(e)}")
    
    # Basic retrieval with default parameters
    print("\n2. BASIC RETRIEVAL (Default Method)")
    print("-" * 40)
    try:
        results = client.retriever.retrieve(
            query="What is machine learning?",
        )
        print(f"Retrieved {len(results.get('documents', []))} document(s)")
        _print_documents_summary(results.get("documents", []))
    except Exception as e:
        print(f"Error during basic retrieval: {e}")
        print(f"Error type: {type(e)}")
    
    # Using different retrieval methods
    print("\n3. SEMANTIC RETRIEVAL")
    print("-" * 40)
    try:
        results = client.retriever.retrieve(
            query="How do neural networks work?",
            method="semantic",
            k=3
        )
        print(f"Retrieved {len(results.get('documents', []))} document(s) using semantic search")
        _print_documents_summary(results.get("documents", []))
    except Exception as e:
        print(f"Error during semantic retrieval: {e}")
        print(f"Error type: {type(e)}")
    
    # Using filters
    print("\n4. FILTERED RETRIEVAL")
    print("-" * 40)
    try:
        results = client.retriever.retrieve(
            query="Python programming examples",
            method="hybrid",
            filter={"category": "programming"},
            k=3
        )
        print(f"Retrieved {len(results.get('documents', []))} document(s) with filter")
        _print_documents_summary(results.get("documents", []))
    except Exception as e:
        print(f"Error during filtered retrieval: {e}")
        print(f"Error type: {type(e)}")
    
    # Using score threshold
    print("\n5. RETRIEVAL WITH SCORE THRESHOLD")
    print("-" * 40)
    try:
        results = client.retriever.retrieve(
            query="Deep learning with TensorFlow",
            method="semantic",
            score_threshold=0.7,
            k=5
        )
        print(f"Retrieved {len(results.get('documents', []))} document(s) with high similarity")
        _print_documents_summary(results.get("documents", []))
    except Exception as e:
        print(f"Error during threshold retrieval: {e}")
        print(f"Error type: {type(e)}")
    
    # Summary
    print("\n" + "="*80)
    print("Simba SDK - RetrieveManager Demo Completed".center(80))
    print("="*80 + "\n")

def _print_documents_summary(documents, max_docs=3, max_content_len=100):
    """Helper function to print a summary of retrieved documents."""
    if not documents:
        print("  No documents found")
        return
        
    for i, doc in enumerate(documents[:max_docs]):
        # Extract content and metadata
        content = doc.get("page_content", "")
        metadata = doc.get("metadata", {})
        
        # Truncate content if needed
        if len(content) > max_content_len:
            content = content[:max_content_len] + "..."
            
        # Print document info
        print(f"\n  Document {i+1}:")
        print(f"  {'Content:':<10} {content}")
        print(f"  {'Metadata:':<10} {', '.join([f'{k}={v}' for k, v in metadata.items()])}")
    
    # Print message if there are more documents
    if len(documents) > max_docs:
        print(f"\n  ... and {len(documents) - max_docs} more document(s)")

if __name__ == "__main__":
    main()
