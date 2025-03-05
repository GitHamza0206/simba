# Simba Client  

Python client for interacting with the Simba document processing API.

## Installation

### Using pip

```bash
pip install simba-client
```

### Development Installation

For development purposes, you can install the package directly from the repository:

```bash
# Clone the repository
git clone https://github.com/GitHamza0206/simba.git
cd simba_sdk

# Install using Poetry
poetry install

# Alternatively, install in development mode with pip
pip install -e .
```

## Quick Start

```python
from simba_sdk import SimbaClient

# Initialize the client
client = SimbaClient(
    api_url="https://api.simba.example.com",
    api_key="your-api-key"
)

# Upload a document
doc_result = client.document.create_from_file("path/to/your/document.pdf")
document_id = doc_result["id"]

# Parse the document
# Use synchronous parsing for immediate results
parse_result = client.parser.parse_document(document_id, sync=True)

# Or asynchronous parsing for background processing
async_result = client.parser.parse_document(document_id, sync=False)
task_id = async_result["task_id"]

# Check the status of an asynchronous task
task_status = client.parser.get_task_status(task_id)

# Extract tables from a document
tables = client.parser.extract_tables(document_id)
```

## Features

- Document Management (upload, retrieve, list, delete)
- Document Parsing (synchronous and asynchronous)
- Natural Language Querying

## Documentation

For detailed documentation, please visit [simba-client.readthedocs.io](https://simba-client.readthedocs.io) or refer to the docs directory in this repository.

## API Reference

### SimbaClient

The main client for interacting with the Simba API.

```python
client = SimbaClient(
    api_url="https://api.simba.example.com",
    api_key="your-api-key",
    timeout=60
)
```

### DocumentManager

Handles document operations (accessible via `client.document`).

- `create(file_path)`: Upload a document from a file path
- `create_from_file(file)`: Upload a document from a file object
- `get(document_id)`: Retrieve a document by ID
- `list()`: List all documents
- `delete(document_id)`: Delete a document

### ParserManager

Handles document parsing operations (accessible via `client.parser`).

- `parse_document(document_id, sync=True)`: Parse a document
- `extract_tables(document_id)`: Extract tables from a document
- `extract_entities(document_id)`: Extract entities from a document
- `extract_forms(document_id)`: Extract form fields from a document
- `extract_text(document_id)`: Extract text content from a document
- `parse_query(document_id, query)`: Extract information based on a natural language query

## Development

### Setup Development Environment

```bash
# Install Poetry if you don't have it
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies including development dependencies
poetry install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=simba_sdk

# Run specific tests
poetry run pytest tests/test_document.py
```

### Building Documentation

```bash
# Build the documentation
poetry run mkdocs build

# Serve the documentation locally
poetry run mkdocs serve
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
