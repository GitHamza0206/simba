# Simba Client (formerly simba_sdk)

A Python client for interacting with the Simba document processing API.

## Installation

### Using pip

```bash
pip install simba-client
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/GitHamza0206/simba.git
cd simba

# Install dependencies with Poetry
poetry install
```

## Quick Start

```python
from simba_sdk import SimbaClient

# Initialize the client
client = SimbaClient(
    api_url="https://your-api.example.com",
    api_key="your-api-key"
)

# Upload a document
with open("document.pdf", "rb") as f:
    result = client.documents.create_from_file(f, "document.pdf")
    document_id = result["document_id"]

# Parse a document synchronously
parsing_result = client.parser.parse_sync(document_id)

# Parse a document asynchronously
task = client.parser.parse(document_id)
task_id = task["task_id"]

# Check the status of a parsing task
task_status = client.parser.get_task(task_id)

# Generate an embedding for semantic search
embedding_result = client.embedding.embed_document(document_id)

# Perform a similarity search
search_results = client.embedding.get_similarity_search(
    document_id, 
    "financial projections for next quarter",
    limit=3
)
```

## Features

- **Document Management**: Upload, download, list, and delete documents
- **Document Parsing**: Extract structured data from documents, including tables, forms, and entities
- **Document Embeddings**: Generate vector embeddings for documents to enable semantic search
- **Authentication**: Secure API access with API keys
- **Error Handling**: Robust error handling for API requests

## Documentation

For more detailed information, check out the documentation:

- [SimbaClient API Reference](docs/api_reference.md)
- [DocumentManager API Reference](docs/api_reference.md#documentmanager)
- [ParserManager API Reference](docs/api_reference.md#parsermanager)
- [EmbeddingManager API Reference](docs/api_reference.md#embeddingmanager)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/simba-client.git
cd simba-client

# Install dependencies with Poetry
poetry install
```

### Run Tests

```bash
poetry run pytest
```

### Build Documentation

```bash
poetry run sphinx-build docs/source docs/build
```

## License

This project is licensed under the MIT License.
