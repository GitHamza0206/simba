#!/usr/bin/env python
"""
Embedding Example - Demonstrates how to use the embedding functionality in Simba Client.

This example shows how to:
1. Upload a document
2. Create an embedding for the document
3. Perform a similarity search
4. List all embeddings
5. Get detailed information about an embedding
6. Delete an embedding

Make sure to set the SIMBA_API_URL and SIMBA_API_KEY environment variables.
"""

import os
import sys
import time
from pprint import pprint

# Add the parent directory to the path to import simba_sdk when running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simba_sdk import SimbaClient

# Get API credentials from environment variables
API_URL = os.environ.get("SIMBA_API_URL")
API_KEY = os.environ.get("SIMBA_API_KEY")

# Path to a sample PDF document
SAMPLE_DOCUMENT_PATH = os.path.join(os.path.dirname(__file__), "sample_document.pdf")

def main():
    """Run the embedding example."""
    if not API_URL or not API_KEY:
        print("Please set the SIMBA_API_URL and SIMBA_API_KEY environment variables.")
        sys.exit(1)
    
    # Initialize the Simba client
    client = SimbaClient(
        api_url=API_URL,
        api_key=API_KEY
    )
    
    print("Simba Embedding Example")
    print("======================")
    
    document_id = None
    
    # Check if the sample document exists
    if os.path.exists(SAMPLE_DOCUMENT_PATH):
        # Upload the sample document
        print(f"\n1. Uploading document: {SAMPLE_DOCUMENT_PATH}")
        try:
            result = client.documents.create_from_path(SAMPLE_DOCUMENT_PATH)
            document_id = result["document_id"]
            print(f"   Document uploaded with ID: {document_id}")
        except Exception as e:
            print(f"   Error uploading document: {e}")
            # Try to list documents to get an ID to use
            try:
                docs = client.documents.list(limit=1)
                if docs["documents"]:
                    document_id = docs["documents"][0]["id"]
                    print(f"   Using existing document with ID: {document_id}")
            except Exception as e2:
                print(f"   Error listing documents: {e2}")
    else:
        # If sample document doesn't exist, list available documents
        print("\n1. Sample document not found. Listing available documents...")
        try:
            docs = client.documents.list(limit=5)
            if docs["documents"]:
                document_id = docs["documents"][0]["id"]
                print(f"   Using existing document with ID: {document_id}")
                for i, doc in enumerate(docs["documents"][:5]):
                    print(f"   {i+1}. ID: {doc['id']}, Name: {doc.get('name', 'Unnamed')}")
            else:
                print("   No documents found. Please upload a document first.")
                sys.exit(1)
        except Exception as e:
            print(f"   Error listing documents: {e}")
            sys.exit(1)
    
    if not document_id:
        print("No document available. Exiting.")
        sys.exit(1)
        
    # Create an embedding for the document
    print(f"\n2. Creating embedding for document {document_id}")
    try:
        result = client.embedding.embed_document(document_id)
        print(f"   Embedding created successfully")
        print(f"   Response: {result}")
    except Exception as e:
        print(f"   Error creating embedding: {e}")
        # Check if embedding already exists
        try:
            embedding = client.embedding.get_embedding(document_id)
            if embedding:
                print(f"   Embedding already exists for document {document_id}")
        except:
            print("   Could not verify if embedding exists")
    
    # Retrieve embedding information
    print(f"\n3. Retrieving embedding information for document {document_id}")
    try:
        embedding = client.embedding.get_embedding(document_id)
        print("   Embedding information:")
        pprint(embedding)
    except Exception as e:
        print(f"   Error retrieving embedding: {e}")
    
    # List all embeddings
    print("\n4. Listing all embeddings")
    try:
        embeddings = client.embedding.list_embeddings(limit=10)
        print(f"   Found {len(embeddings.get('embeddings', []))} embeddings")
        for i, emb in enumerate(embeddings.get("embeddings", [])[:5]):
            print(f"   {i+1}. Document ID: {emb.get('document_id')}, Model: {emb.get('model', 'unknown')}")
    except Exception as e:
        print(f"   Error listing embeddings: {e}")
    
    # Perform similarity search
    print(f"\n5. Performing similarity search on document {document_id}")
    search_query = "financial analysis and revenue forecasts"
    print(f"   Search query: '{search_query}'")
    try:
        results = client.embedding.get_similarity_search(document_id, search_query, limit=3)
        print(f"   Found {len(results.get('results', []))} matches")
        for i, result in enumerate(results.get("results", [])):
            print(f"   Match {i+1}: Score {result.get('score', 0):.4f}")
            content = result.get('content', '')[:150]
            if content:
                print(f"   Content: {content}...")
            print()
    except Exception as e:
        print(f"   Error performing similarity search: {e}")
    
    # Batch embedding (optional demonstration)
    show_batch = input("\nDo you want to demonstrate batch embedding? (y/n): ").lower().strip() == 'y'
    if show_batch:
        print("\n6. Demonstrating batch embedding")
        try:
            # List documents to get IDs for batch embedding
            docs = client.documents.list(limit=5)
            if len(docs.get("documents", [])) > 1:
                doc_ids = [doc["id"] for doc in docs["documents"][:3]]
                print(f"   Embedding {len(doc_ids)} documents: {doc_ids}")
                
                # Start batch embedding
                batch_result = client.embedding.embed_documents(doc_ids)
                print(f"   Batch embedding started with task ID: {batch_result.get('task_id')}")
                
                # Check status a few times
                task_id = batch_result.get('task_id')
                if task_id:
                    for i in range(3):
                        print(f"   Checking status ({i+1}/3)...")
                        try:
                            status = client.embedding.get_embedding_status(task_id)
                            print(f"   Status: {status.get('state')}")
                            if status.get('state') in ['SUCCESS', 'FAILURE']:
                                break
                        except Exception as e:
                            print(f"   Error checking status: {e}")
                            break
                        time.sleep(2)
            else:
                print("   Not enough documents for batch demonstration")
        except Exception as e:
            print(f"   Error in batch embedding demonstration: {e}")
    
    # Delete embedding (optional, ask first)
    delete_emb = input("\nDo you want to delete the embedding for demonstration? (y/n): ").lower().strip() == 'y'
    if delete_emb:
        print(f"\n7. Deleting embedding for document {document_id}")
        try:
            result = client.embedding.delete_embedding(document_id)
            print(f"   Embedding deleted successfully")
            print(f"   Response: {result}")
        except Exception as e:
            print(f"   Error deleting embedding: {e}")
    
    print("\nEmbedding example completed.")

if __name__ == "__main__":
    main() 