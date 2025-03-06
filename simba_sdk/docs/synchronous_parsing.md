# Synchronous Parsing Guide

This guide explains how to use the synchronous parsing feature in the Simba Client (formerly simba_sdk).

## Overview

The Simba Client supports two parsing modes:

1. **Asynchronous Parsing (Default)**: Parsing tasks are queued and processed in the background. You need to poll for results.
2. **Synchronous Parsing (New)**: Parsing is performed immediately and results are returned in the same request.

## When to Use Synchronous Parsing

Synchronous parsing is ideal for:

- Processing small documents (< 10 pages)
- Applications requiring immediate results
- Testing and debugging
- Interactive applications where waiting is not desirable

For large documents or batch processing, asynchronous parsing is still recommended.

## Basic Usage

To parse a document synchronously, set the `sync` parameter to `True`:

```python
from simba_sdk import SimbaClient

# Initialize the client
client = SimbaClient(api_url="https://your-server.example.com", api_key="your-key")

# Upload a document
upload_result = client.document_manager.upload_document("path/to/document.pdf")
document_id = upload_result["document_id"]

# Parse the document synchronously
parsing_result = client.parser_manager.parse_document(
    document_id=document_id,
    sync=True  # This enables synchronous parsing
)

# Access the parsed content directly
tables = parsing_result["result"]["tables"]
entities = parsing_result["result"]["entities"]
text = parsing_result["result"]["text"]

print(f"Found {len(tables)} tables and {len(entities)} entities")
```

## Comparison with Asynchronous Parsing

### Asynchronous Parsing

```python
# Asynchronous parsing (default)
parse_task = client.parser_manager.parse_document(
    document_id=document_id,
    sync=False  # This is the default
)

# Get the task ID
task_id = parse_task["task_id"]

# Poll for results
import time
for _ in range(10):
    status = client.parser_manager.get_parse_status(task_id)
    if status["state"] == "SUCCESS":
        result = status["result"]
        print("Parsing completed!")
        break
    elif status["state"] == "FAILURE":
        print(f"Parsing failed: {status.get('error', 'Unknown error')}")
        break
    print("Parsing in progress...")
    time.sleep(5)
```

### Synchronous Parsing

```python
# Synchronous parsing
try:
    result = client.parser_manager.parse_document(
        document_id=document_id,
        sync=True
    )
    print("Parsing completed!")
except Exception as e:
    print(f"Parsing failed: {e}")
```

## Timeout Considerations

Synchronous parsing can take longer for complex documents. You may need to increase the client's timeout:

```python
# Increase the timeout for complex documents
client = SimbaClient(
    api_url="https://your-server.example.com",
    api_key="your-key",
    timeout=300  # 5 minutes (default is 60 seconds)
)
```

## Feature-Specific Synchronous Parsing

You can also use synchronous parsing for specific features:

### Tables

```python
# Extract tables synchronously
tables = client.parser_manager.extract_tables(
    document_id=document_id,
    sync=True
)
```

### Entities

```python
# Extract entities synchronously
entities = client.parser_manager.extract_entities(
    document_id=document_id,
    sync=True
)
```

### Text

```python
# Extract text synchronously
text = client.parser_manager.extract_text(
    document_id=document_id,
    sync=True
)
```

### Forms

```python
# Extract forms synchronously
forms = client.parser_manager.extract_forms(
    document_id=document_id,
    sync=True
)
```

## Error Handling

Synchronous parsing provides immediate error feedback:

```python
try:
    result = client.parser_manager.parse_document(
        document_id=document_id,
        sync=True
    )
    print("Parsing completed successfully!")
except SimbaAPIError as e:
    if e.status_code == 404:
        print(f"Document {document_id} not found")
    elif e.status_code == 422:
        print(f"Invalid document format or content")
    else:
        print(f"API error: {e}")
except SimbaConnectionError as e:
    print(f"Connection timeout: The document may be too large for synchronous parsing")
    print(f"Consider using asynchronous parsing instead")
```

## Best Practices

1. **Document Size**: Use synchronous parsing only for small to medium-sized documents.
2. **Timeouts**: Set an appropriate timeout value based on expected document complexity.
3. **Fallback Strategy**: Implement a fallback to asynchronous parsing if synchronous parsing times out.
4. **Error Handling**: Always include proper error handling for synchronous requests.

## Complete Example

Here's a complete example with proper error handling and fallback strategy:

```python
from simba_sdk import SimbaClient, SimbaConnectionError, SimbaAPIError

def parse_document(client, document_id, prefer_sync=True, timeout=120):
    """
    Parse a document with fallback from synchronous to asynchronous if needed.
    
    Args:
        client: SimbaClient instance
        document_id: ID of the document to parse
        prefer_sync: Whether to try synchronous parsing first
        timeout: Timeout in seconds for synchronous parsing
        
    Returns:
        Parsing result dictionary
    """
    if prefer_sync:
        # Try synchronous parsing first
        try:
            # Create a client with appropriate timeout
            sync_client = SimbaClient(
                api_url=client.api_url,
                api_key=client.api_key,
                timeout=timeout
            )
            
            result = sync_client.parser_manager.parse_document(
                document_id=document_id,
                sync=True
            )
            print("Synchronous parsing completed successfully")
            return result
            
        except SimbaConnectionError:
            print("Synchronous parsing timed out, falling back to asynchronous parsing")
            # Fall back to asynchronous parsing
        except SimbaAPIError as e:
            if e.status_code == 413:  # Request Entity Too Large
                print("Document too large for synchronous parsing, falling back to asynchronous")
                # Fall back to asynchronous parsing
            else:
                # Re-raise other API errors
                raise
    
    # Asynchronous parsing (either as primary strategy or fallback)
    parse_task = client.parser_manager.parse_document(
        document_id=document_id,
        sync=False
    )
    
    task_id = parse_task["task_id"]
    print(f"Asynchronous parsing started with task ID: {task_id}")
    
    # Implement polling for results
    import time
    for attempt in range(12):  # Poll for up to 1 minute (5s × 12)
        status = client.parser_manager.get_parse_status(task_id)
        if status["state"] == "SUCCESS":
            print(f"Asynchronous parsing completed successfully after {attempt + 1} attempts")
            return status
        elif status["state"] == "FAILURE":
            error_msg = status.get("error", "Unknown error")
            raise Exception(f"Parsing failed: {error_msg}")
        
        print(f"Parsing in progress... (attempt {attempt + 1}/12)")
        time.sleep(5)
    
    raise Exception("Parsing timed out after 1 minute")

# Usage example
client = SimbaClient(api_url="https://your-server.example.com", api_key="your-key")
document_id = "your-document-id"

try:
    result = parse_document(client, document_id)
    # Process the results
    tables = result["result"]["tables"]
    entities = result["result"]["entities"]
    print(f"Found {len(tables)} tables and {len(entities)} entities")
except Exception as e:
    print(f"Error: {e}")
```

This approach provides the best of both worlds: it attempts fast synchronous parsing when possible but falls back to reliable asynchronous parsing when necessary. 