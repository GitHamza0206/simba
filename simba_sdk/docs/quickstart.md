# Quick Start Guide

This guide will help you get started with the Simba Client (formerly simba_sdk) to process documents quickly.

## Installation

First, install the package:

```bash
pip install simba-client
```

For detailed installation instructions, see the [Installation Guide](./installation.md).

## Basic Usage

### 1. Initialize the Client

```python
from simba_sdk import SimbaClient

# Initialize the client with your API credentials
client = SimbaClient(
    api_url="https://your-simba-server.example.com",
    api_key="your-api-key-here"
)
```

### 2. Upload a Document

```python
# Upload a document from a local file
upload_result = client.document_manager.upload_document("path/to/your/document.pdf")

# Get the document ID for later use
document_id = upload_result["document_id"]
print(f"Uploaded document with ID: {document_id}")
```

### 3. Process a Document

You can process documents either synchronously (immediate results) or asynchronously (background processing).

#### Synchronous Processing (Recommended for small documents)

```python
# Parse the document synchronously
try:
    result = client.parser_manager.parse_document(
        document_id=document_id,
        sync=True  # Process immediately and wait for results
    )
    
    # Access the results
    print(f"Document processed successfully!")
    print(f"Found {len(result['result']['tables'])} tables")
    print(f"Found {len(result['result']['entities'])} entities")
    
except Exception as e:
    print(f"Error processing document: {e}")
```

#### Asynchronous Processing (Recommended for large documents)

```python
# Start an asynchronous parsing job
parse_task = client.parser_manager.parse_document(
    document_id=document_id,
    sync=False  # Start a background task (default)
)

# Get the task ID
task_id = parse_task["task_id"]
print(f"Started parsing task with ID: {task_id}")

# Check the task status
import time

for _ in range(10):  # Poll for up to 50 seconds
    status = client.parser_manager.get_parse_status(task_id)
    
    if status["state"] == "SUCCESS":
        # Processing completed
        result = status["result"]
        print(f"Document processed successfully!")
        print(f"Found {len(result['tables'])} tables")
        print(f"Found {len(result['entities'])} entities")
        break
        
    elif status["state"] == "FAILURE":
        # Processing failed
        print(f"Processing failed: {status.get('error', 'Unknown error')}")
        break
        
    else:
        # Still processing
        print("Processing in progress...")
        time.sleep(5)  # Wait 5 seconds before checking again
```

### 4. Extract Specific Information

The Simba Client provides methods to extract specific types of information:

#### Extract Tables

```python
# Extract tables from the document
tables = client.parser_manager.extract_tables(
    document_id=document_id,
    sync=True  # Use synchronous processing
)

# Print table information
for i, table in enumerate(tables["result"]["tables"]):
    print(f"Table {i+1}: {len(table['rows'])} rows × {len(table['columns'])} columns")
```

#### Extract Entities

```python
# Extract entities from the document
entities = client.parser_manager.extract_entities(
    document_id=document_id,
    sync=True
)

# Print entity information
for entity in entities["result"]["entities"]:
    print(f"Entity: {entity['text']} (Type: {entity['type']})")
```

#### Extract Text

```python
# Extract all text from the document
text_result = client.parser_manager.extract_text(
    document_id=document_id,
    sync=True
)

# Print the first 200 characters of the text
text = text_result["result"]["text"]
print(f"Document text (preview): {text[:200]}...")
```

### 5. Document Management

#### List Documents

```python
# Get a list of all documents
documents = client.document_manager.list_documents(limit=10)

# Print document information
for doc in documents:
    print(f"Document ID: {doc['id']}, Name: {doc.get('name', 'Unnamed')}")
```

#### Download a Document

```python
# Download the document to a local file
output_path = "downloaded_document.pdf"
client.document_manager.download_document(
    document_id=document_id,
    output_path=output_path
)
print(f"Document downloaded to {output_path}")
```

#### Delete a Document

```python
# Delete a document when you're done with it
client.document_manager.delete_document(document_id)
print(f"Document {document_id} deleted")
```

### Document Embeddings

Generate embeddings for semantic search:

```python
# Generate an embedding for a document
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
```

## Complete Example

Here's a complete example that ties everything together:

```python
import time
from simba_sdk import SimbaClient, SimbaAPIError, SimbaConnectionError

def process_document(file_path, api_url, api_key):
    """
    Process a document and extract information from it.
    
    Args:
        file_path: Path to the document file
        api_url: Simba API URL
        api_key: Simba API Key
        
    Returns:
        Extracted information from the document
    """
    # Initialize the client
    client = SimbaClient(
        api_url=api_url,
        api_key=api_key,
        timeout=120  # Increase timeout for larger documents
    )
    
    try:
        # Upload the document
        print(f"Uploading document: {file_path}")
        upload_result = client.document_manager.upload_document(file_path)
        document_id = upload_result["document_id"]
        print(f"Document uploaded with ID: {document_id}")
        
        # Try synchronous parsing first
        try:
            print("Attempting synchronous parsing...")
            result = client.parser_manager.parse_document(
                document_id=document_id,
                sync=True
            )
            print("Synchronous parsing completed")
            
        except (SimbaConnectionError, SimbaAPIError) as e:
            print(f"Synchronous parsing failed: {e}")
            print("Falling back to asynchronous parsing...")
            
            # Fall back to asynchronous parsing
            parse_task = client.parser_manager.parse_document(
                document_id=document_id,
                sync=False
            )
            task_id = parse_task["task_id"]
            
            # Poll for results
            for attempt in range(12):  # Poll for up to 1 minute
                print(f"Checking task status (attempt {attempt+1}/12)...")
                status = client.parser_manager.get_parse_status(task_id)
                
                if status["state"] == "SUCCESS":
                    result = status
                    print("Asynchronous parsing completed")
                    break
                elif status["state"] == "FAILURE":
                    raise Exception(f"Parsing failed: {status.get('error', 'Unknown error')}")
                
                time.sleep(5)
            else:
                raise Exception("Parsing timed out after 1 minute")
        
        # Extract and return relevant information
        return {
            "document_id": document_id,
            "tables": result["result"]["tables"],
            "entities": result["result"]["entities"],
            "text": result["result"]["text"][:500] + "..." if len(result["result"]["text"]) > 500 else result["result"]["text"]
        }
        
    except Exception as e:
        print(f"Error processing document: {e}")
        raise
    
# Usage
if __name__ == "__main__":
    try:
        result = process_document(
            file_path="example.pdf",
            api_url="https://your-simba-server.example.com",
            api_key="your-api-key-here"
        )
        
        # Print summary of results
        print("\nDocument Processing Results:")
        print(f"Document ID: {result['document_id']}")
        print(f"Tables found: {len(result['tables'])}")
        print(f"Entities found: {len(result['entities'])}")
        print(f"Text preview: {result['text']}")
        
    except Exception as e:
        print(f"Failed to process document: {e}")
```

## Next Steps

Now that you're familiar with the basics, here are some resources to help you go further:

- [API Reference](./api_reference.md) - Detailed documentation of all available methods
- [Synchronous Parsing Guide](./synchronous_parsing.md) - Learn more about synchronous document processing
- [Document Management](./document_management.md) - Advanced document management features
- [Error Handling](./error_handling.md) - How to handle errors properly

For help with specific issues, see the [Troubleshooting Guide](./troubleshooting.md). 