# Simba SDK Parsing Documentation

The Simba SDK provides powerful document parsing capabilities through the `ParserManager` class. This guide explains how to use both synchronous and asynchronous parsing methods to extract meaningful information from your documents.

## Introduction

The `ParserManager` allows you to:

- Parse documents using various parsing engines
- Extract structured data such as tables, entities, and forms
- Perform text extraction with layout preservation
- Execute natural language queries against documents

## Initialization

First, initialize the `SimbaClient` with your API credentials:

```python
from simba_sdk import SimbaClient

client = SimbaClient(api_url="https://api.example.com", api_key="your_api_key")
```

The `ParserManager` is accessible through the `parser` property of the `SimbaClient`:

```python
parser_manager = client.parser
```

## Synchronous vs. Asynchronous Parsing

The Simba SDK supports both synchronous and asynchronous parsing:

- **Synchronous Parsing**: Processes the document immediately and returns the result once parsing is complete. Best for smaller documents when immediate results are needed.
- **Asynchronous Parsing**: Submits a parsing task to be processed in the background and returns a task ID. Best for larger documents or when you want to avoid blocking your application.

## Synchronous Parsing

Use synchronous parsing when you need immediate results:

```python
# Parse a document synchronously (default behavior)
result = client.parser.parse_document("document_id", sync=True)

# The result contains the parsed document data
print(f"Parsing status: {result['result']['parsing_status']}")
print(f"Number of chunks: {result['result']['num_chunks']}")
```

> **Note**: The synchronous parsing endpoint expects the document_id as a query parameter. The SDK handles this automatically, but if you're seeing a 422 error, ensure that your backend API supports synchronous parsing and is configured to accept the document_id parameter correctly.

## Asynchronous Parsing

Use asynchronous parsing for large documents or to avoid blocking:

```python
# Parse a document asynchronously
task_result = client.parser.parse_document("document_id", sync=False)

# Get the task ID for later status checks
task_id = task_result["task_id"]
print(f"Task ID: {task_id}")

# Check the status of the task
task_status = client.parser.get_task_status(task_id)
print(f"Task status: {task_status['status']}")
```

### Waiting for Completion

You can wait for an asynchronous task to complete:

```python
# Parse and wait for completion
result = client.parser.parse_document(
    "document_id", 
    sync=False,
    wait_for_completion=True,
    polling_interval=2,  # Check every 2 seconds
    timeout=60           # Wait up to 60 seconds
)

# If wait_for_completion is True, the result will contain
# the final parsing result, similar to synchronous parsing
print(f"Task completed with status: {result['status']}")
print(f"Result: {result['result']}")
```

## Feature Extraction

The `ParserManager` provides specialized methods for extracting specific features from documents:

### Extract Tables

```python
# Extract tables synchronously
tables = client.parser.extract_tables("document_id", sync=True)

# Extract tables asynchronously
tables_task = client.parser.extract_tables("document_id", sync=False)
```

### Extract Entities

```python
# Extract named entities (people, organizations, dates, etc.)
entities = client.parser.extract_entities("document_id")

for entity in entities.get("entities", []):
    print(f"Type: {entity['type']}, Text: {entity['text']}")
```

### Extract Form Fields

```python
# Extract form fields from documents
forms = client.parser.extract_forms("document_id", form_type="application")

for field in forms.get("form_fields", []):
    print(f"Field: {field['name']}, Value: {field['value']}")
```

### Extract Text with Layout

```python
# Extract text while preserving structural information
text = client.parser.extract_text("document_id", structured=True, include_layout=True)

print(f"Full text: {text['text']}")
for section in text.get("sections", []):
    print(f"Section: {section['title']}")
    print(f"Content: {section['content']}")
```

## Natural Language Querying

You can ask natural language questions about document content:

```python
# Query a document with a natural language question
query_result = client.parser.parse_query(
    "document_id", 
    "What is the total revenue for Q3 2023?"
)

print(f"Query: {query_result['query']}")
print(f"Answer: {query_result['result']}")
```

## Managing Parsing Tasks

You can view and manage all parsing tasks:

```python
# Get all active parsing tasks
all_tasks = client.parser.get_all_tasks()

print(f"Active tasks: {len(all_tasks.get('active', {}))}")
print(f"Reserved tasks: {len(all_tasks.get('reserved', {}))}")
print(f"Scheduled tasks: {len(all_tasks.get('scheduled', {}))}")
```

## Error Handling

The SDK includes proper error handling for parsing operations:

```python
try:
    result = client.parser.parse_document("document_id")
    print(f"Parsing successful: {result}")
except Exception as e:
    print(f"Parsing failed: {e}")
```

## Troubleshooting

If you encounter a 422 Unprocessable Entity error when using synchronous parsing, check the following:

1. Ensure your backend API has the synchronous parsing endpoint implemented
2. Verify that the endpoint is configured to accept the document_id as a query parameter
3. Make sure the document with the specified ID exists in your system
4. Check if the document is in a proper state for parsing

## Best Practices

1. **Choose the right parsing mode**:
   - Use synchronous parsing for small documents and immediate needs
   - Use asynchronous parsing for large documents or to avoid blocking

2. **Resource considerations**:
   - Parsing large documents can be resource-intensive
   - Consider using asynchronous parsing for documents over 10MB

3. **Error handling**:
   - Always implement proper error handling around parsing operations
   - Check task status for asynchronous operations

4. **Performance tips**:
   - Use specialized extraction methods when you only need specific features
   - Set realistic timeouts when using `wait_for_completion=True` 