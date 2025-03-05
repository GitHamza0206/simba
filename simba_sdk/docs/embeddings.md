# Document Embeddings

This guide explains how to use the embedding functionality in the Simba Client to generate and manage vector embeddings for your documents.

> **Note on API Endpoints**: The Simba embedding API endpoints have been updated to match the server implementation. If you were directly calling API endpoints in your code (not recommended), you'll need to update them. If you're using the `EmbeddingManager` class as documented here, no changes are needed as the SDK handles this for you.

## What are Embeddings?

Embeddings are vector representations of documents or text that capture semantic meaning. They're useful for:

- Semantic search (finding documents with similar meaning)
- Document clustering
- Recommendation systems
- Question answering systems

## Basic Usage

### Creating an Embedding for a Document

To create an embedding for a single document:

```python
from simba_sdk import SimbaClient

client = SimbaClient(api_url="https://your-api.example.com", api_key="your-api-key")

# Generate embeddings for a document
result = client.embedding.embed_document("document_id")
print(f"Embedding created with ID: {result['embedding_id']}")
```

### Listing All Embeddings

To retrieve a list of all embedded documents:

```python
# List all embeddings
embeddings = client.embedding.list_embeddings(limit=20)

print(f"Found {len(embeddings['embeddings'])} embedded documents:")
for embedding in embeddings["embeddings"]:
    print(f"Document ID: {embedding['document_id']}")
```

### Getting a Specific Embedding

To retrieve detailed information about a specific embedding:

```python
# Get embedding information
embedding = client.embedding.get_embedding("document_id")

print(f"Embedding model: {embedding['model']}")
print(f"Dimensions: {embedding['dimensions']}")
```

## Batch Operations

### Embedding Multiple Documents

To generate embeddings for multiple documents at once:

```python
# Embed multiple documents
document_ids = ["doc_id_1", "doc_id_2", "doc_id_3"]
batch_result = client.embedding.embed_documents(document_ids)

# Get the task ID for tracking progress
task_id = batch_result["task_id"]
print(f"Batch embedding started with task ID: {task_id}")

# Check the task status
import time
for _ in range(10):
    status = client.embedding.get_embedding_status(task_id)
    if status["state"] == "SUCCESS":
        print("Embedding complete!")
        break
    elif status["state"] == "FAILURE":
        print(f"Embedding failed: {status.get('error')}")
        break
    print("Still processing...")
    time.sleep(2)
```

### Embedding All Documents

To generate embeddings for all documents in your system:

```python
# Embed all documents
result = client.embedding.embed_all_documents()
task_id = result["task_id"]
print(f"Embedding all documents with task ID: {task_id}")
```

## Choosing Embedding Models

You can specify which embedding model to use:

```python
# Use a specific embedding model
result = client.embedding.embed_document(
    "document_id", 
    model="text-embedding-ada-002"  # Or any other supported model
)
```

## Similarity Search

Once you have embeddings, you can perform semantic searches:

```python
# Search for similar content
query = "financial reports from Q2 2023"
search_results = client.embedding.get_similarity_search(
    "document_id",  # Document to search within
    query,          # Search query
    limit=5         # Number of results to return
)

# Display search results
for i, result in enumerate(search_results["results"]):
    print(f"Result {i+1}: Score {result['score']}")
    print(f"Content: {result['content'][:100]}...")
    print()
```

## Managing Embeddings

### Deleting an Embedding

To delete an embedding for a specific document:

```python
# Delete embedding for a specific document
result = client.embedding.delete_embedding("document_id")
print(f"Embedding deleted: {result['status']}")
```

### Deleting All Embeddings

To delete all embeddings in your system:

```python
# Delete all embeddings
result = client.embedding.delete_all_embeddings()
print(f"Deleted {result['count']} embeddings")
```

## Monitoring Embedding Tasks

For batch operations, you can monitor the progress:

```python
# Check the status of an embedding task
status = client.embedding.get_embedding_status("task_id")

if status["state"] == "SUCCESS":
    print("Task completed successfully")
    # Access results if available
    if "result" in status:
        print(f"Embedded {len(status['result'].get('document_ids', []))} documents")
elif status["state"] == "FAILURE":
    print(f"Task failed: {status.get('error')}")
else:
    print(f"Task is still {status['state']}")
```

## API Endpoints Reference

For developers who need to know the actual API endpoints used:

| Operation | API Endpoint | HTTP Method | Parameters |
|-----------|--------------|------------|------------|
| Embed document | `/embed/document` | POST | `doc_id`: Document ID |
| Get embedding | `/embedded_documents` | GET | `doc_id`: Document ID |
| List embeddings | `/embedded_documents` | GET | `limit`, `offset` |
| Embed multiple documents | `/embed/documents` | POST | JSON body with `document_ids` |
| Delete embedding | `/embed/document` | DELETE | `doc_id`: Document ID |
| Delete all embeddings | `/embed/clear_store` | DELETE | None |
| Get task status | `/embed/task/{task_id}` | GET | None |
| Similarity search | `/embed/search` | GET | `doc_id`, `query`, `limit` |

## Best Practices

1. **Batch Processing**: For large collections, use batch embedding operations rather than individual ones.

2. **Model Selection**: Choose the appropriate embedding model based on your needs:
   - Smaller models are faster but may be less accurate
   - Larger models produce better results but require more processing time

3. **Reuse Embeddings**: Generate embeddings once and reuse them for multiple search operations.

4. **Delete Unused Embeddings**: To save storage, delete embeddings for documents you no longer need.

5. **Update Embeddings When Content Changes**: If a document's content changes, regenerate its embedding to maintain search accuracy.

## Error Handling

Always implement proper error handling when working with embeddings:

```python
try:
    result = client.embedding.embed_document("document_id")
    print("Embedding created successfully")
except Exception as e:
    print(f"Error creating embedding: {e}")
```

## Complete Example

Here's a complete example that demonstrates the embedding functionality:

```python
from simba_sdk import SimbaClient
import time

# Initialize the client
client = SimbaClient(api_url="https://your-api.example.com", api_key="your-api-key")

# Upload a document (if not already uploaded)
with open("document.pdf", "rb") as f:
    upload_result = client.documents.create_from_file(f, "document.pdf")
    document_id = upload_result["document_id"]

# Generate embeddings for the document
try:
    embedding_result = client.embedding.embed_document(document_id)
    print(f"Embedding created with ID: {embedding_result['embedding_id']}")
    
    # Perform a similarity search
    query = "financial projections for next quarter"
    search_results = client.embedding.get_similarity_search(document_id, query, limit=3)
    
    print("\nSearch results:")
    for i, result in enumerate(search_results["results"]):
        print(f"{i+1}. Score: {result['score']:.4f}")
        print(f"   {result['content'][:150]}...")
        print()
    
except Exception as e:
    print(f"Error in embedding process: {e}")
``` 