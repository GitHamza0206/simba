# Simba SDK 

This is a Python SDK for the Simba Knowledge Management System.

## Installation

```bash
pip install simba-sdk
```

## Usage

### Initialize the Client

```python
from simba_sdk import SimbaClient

# Initialize the client with your Simba API URL and optional API key
client = SimbaClient(api_url="https://your-simba-instance.com/api/v1", api_key="your-api-key")
```

### Document Management

The SDK provides comprehensive document management capabilities through the `documents` property of the client:

#### Upload and Ingest a Document

```python
# Upload a file from disk
document = client.documents.create("path/to/document.pdf")
document_id = document["document_id"]

# Upload with metadata
document = client.documents.create(
    "path/to/document.pdf", 
    metadata={"author": "John Doe", "category": "Research"}
)
```

#### Create a Document from Text

```python
# Create a document from raw text
document = client.documents.create_from_text(
    text="This is the content of my document.",
    name="example.txt",
    metadata={"source": "User input"}
)
```

#### Get Document Details

```python
# Retrieve a document by ID
document = client.documents.get(document_id)
print(document["name"])
print(document["metadata"])
```

#### List Documents

```python
# List all documents
documents = client.documents.list()
for doc in documents["items"]:
    print(f"{doc['document_id']}: {doc['name']}")

# With pagination
documents = client.documents.list(page=2, page_size=10)

# With filters
documents = client.documents.list(filters={"author": "John Doe"})
```

#### Update Document Metadata

```python
# Update metadata
updated_document = client.documents.update(
    document_id,
    metadata={"status": "reviewed", "rating": 5}
)
```

#### Delete a Document

```python
# Delete a document
result = client.documents.delete(document_id)
print(result["status"])  # Should be "deleted"
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/simba-sdk.git
cd simba-sdk

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests

```bash
pytest
```

## License

[Your License Info Here]
