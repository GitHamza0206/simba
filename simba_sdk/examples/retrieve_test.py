#!/usr/bin/env python
"""
Test script to verify the fixed retrieve functionality in the Simba SDK.
"""

from simba_sdk import SimbaClient, RetrieveManager

# Initialize the client with the correct URL
API_URL = "http://localhost:8000"  # Use your Simba API URL
client = SimbaClient(API_URL)

# Test the retrieve functionality
print("Testing retrieve functionality...")
try:
    results = client.retriever.retrieve(
        query="who is john?",
        strategy="semantic",
        top_k=5
    )
    print("Retrieve successful!")
    print(f"Results: {results}")
except Exception as e:
    print(f"Error during retrieve: {e}")
    print(f"Error type: {type(e)}")

# Test the get_retrieval_strategies functionality
print("\nTesting get_retrieval_strategies functionality...")
try:
    strategies = client.retriever.get_retrieval_strategies()
    print("Get retrieval strategies successful!")
    print(f"Strategies: {strategies}")
except Exception as e:
    print(f"Error during get_retrieval_strategies: {e}")
    print(f"Error type: {type(e)}") 