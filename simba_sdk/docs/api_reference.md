# API Reference

This document provides detailed information about the classes and methods available in the Simba Client (formerly simba_sdk).

## SimbaClient

The main client class for interacting with the Simba API.

```python
from simba_sdk import SimbaClient

client = SimbaClient(api_url="https://api.example.com", api_key="your-api-key")
```

### Parameters

- `api_url` (str): The URL of the Simba API server
- `api_key` (str): Your API key for authentication
- `timeout` (int, optional): Request timeout in seconds. Default: 60
- `verify_ssl` (bool, optional): Whether to verify SSL certificates. Default: True

### Properties

- `document_manager`: Access the document management API
- `parser_manager`: Access the document parsing API

### Methods

#### `health_check()`

Check if the Simba API is operational.

**Returns**:
- `bool`: True if the API is operational, False otherwise

#### `get_version()`

Get the version of the Simba API.

**Returns**:
- `str`: The version string

## DocumentManager

Handles document upload, download, and management operations.

```python
# Access through the SimbaClient
doc_manager = client.document_manager
```

### Methods

#### `upload_document(file_path, metadata=None)`

Upload a document to the Simba server.

**Parameters**:
- `file_path` (str): Path to the file to upload
- `metadata` (dict, optional): Additional metadata about the document

**Returns**:
- `dict`: Response containing the document ID and status

#### `get_document(document_id)`

Retrieve a document by its ID.

**Parameters**:
- `document_id` (str): The ID of the document to retrieve

**Returns**:
- `dict`: Document information including metadata

#### `delete_document(document_id)`

Delete a document by its ID.

**Parameters**:
- `document_id` (str): The ID of the document to delete

**Returns**:
- `dict`: Response indicating success or failure

#### `list_documents(limit=100, offset=0)`

List documents available on the server.

**Parameters**:
- `limit` (int, optional): Maximum number of documents to retrieve. Default: 100
- `offset` (int, optional): Offset for pagination. Default: 0

**Returns**:
- `list`: List of document objects

#### `download_document(document_id, output_path=None)`

Download a document file.

**Parameters**:
- `document_id` (str): The ID of the document to download
- `output_path` (str, optional): Path where the document should be saved. If not provided, returns the file content.

**Returns**:
- `bytes` or `str`: File content or path to saved file

## ParserManager

Handles document parsing operations.

```python
# Access through the SimbaClient
parser = client.parser_manager
```

### Methods

#### `parse_document(document_id, sync=False)`

Parse a document using the Simba parsing engine.

**Parameters**:
- `document_id` (str): The ID of the document to parse
- `sync` (bool, optional): Whether to parse synchronously. Default: False

**Returns**:
- If `sync=True`: `dict` with the parsing results
- If `sync=False`: `dict` with a task ID for tracking the parsing job

#### `get_parse_status(task_id)`

Check the status of an asynchronous parsing task.

**Parameters**:
- `task_id` (str): The ID of the parsing task

**Returns**:
- `dict`: Task status information

#### `get_parsers()`

Get a list of available parsers.

**Returns**:
- `list`: Available parsers

#### `extract_tables(document_id, sync=False)`

Extract tables from a document.

**Parameters**:
- `document_id` (str): The ID of the document
- `sync` (bool, optional): Whether to extract synchronously. Default: False

**Returns**:
- `dict`: Extracted tables or task information

#### `extract_entities(document_id, sync=False)`

Extract entities from a document.

**Parameters**:
- `document_id` (str): The ID of the document
- `sync` (bool, optional): Whether to extract synchronously. Default: False

**Returns**:
- `dict`: Extracted entities or task information

#### `extract_text(document_id, sync=False)`

Extract text from a document.

**Parameters**:
- `document_id` (str): The ID of the document
- `sync` (bool, optional): Whether to extract synchronously. Default: False

**Returns**:
- `dict`: Extracted text or task information

#### `extract_forms(document_id, sync=False)`

Extract form data from a document.

**Parameters**:
- `document_id` (str): The ID of the document
- `sync` (bool, optional): Whether to extract synchronously. Default: False

**Returns**:
- `dict`: Extracted form data or task information

## Error Handling

The SDK uses custom exceptions to handle errors:

### SimbaClientError

Base exception for all client errors.

### SimbaAPIError

Raised when the API returns an error response.

```python
try:
    result = client.document_manager.get_document("non-existent-id")
except SimbaAPIError as e:
    print(f"API Error: {e.status_code} - {e.message}")
```

### SimbaConnectionError

Raised when there is a problem connecting to the API.

```python
try:
    client = SimbaClient(api_url="https://invalid-url.example", api_key="invalid-key")
    client.health_check()
except SimbaConnectionError as e:
    print(f"Connection Error: {e}")
``` 