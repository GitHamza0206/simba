# Migrating from simba_sdk to simba-client

This guide will help you migrate your code from the old `simba_sdk` package to the new `simba-client` package.

## Installation Changes

### Old Installation

```bash
pip install simba-sdk
```

### New Installation

```bash
pip install simba-client
```

## Import Changes

The package structure has been cleaned up, but we've maintained backward compatibility in the imports:

```python
# Old imports will continue to work
from simba_sdk import SimbaClient

# New imports are the same
from simba_sdk import SimbaClient
```

## API Changes

### SimbaClient

The `SimbaClient` class remains the same:

```python
# Old code
client = SimbaClient(api_url="https://api.example.com", api_key="your-api-key")

# New code - identical
client = SimbaClient(api_url="https://api.example.com", api_key="your-api-key")
```

### Document Management

The document management API has been slightly renamed for clarity:

```python
# Old code
document = client.documents.create_from_file("path/to/file.pdf")

# New code
document = client.document.create_from_file("path/to/file.pdf")
```

Notice the change from plural `documents` to singular `document`.

### Parsing API Enhancements

The parsing API has been enhanced with clearer options for synchronous vs. asynchronous parsing:

```python
# Old code
result = client.parser.parse_document(document_id)

# New code - synchronous parsing (default)
result = client.parser.parse_document(document_id, sync=True)

# New code - asynchronous parsing
result = client.parser.parse_document(document_id, sync=False)
```

### Feature Extraction Improvements

Feature extraction methods have been updated to support both synchronous and asynchronous extraction:

```python
# Old code
tables = client.parser.extract_tables(document_id)

# New code - synchronous extraction (default)
tables = client.parser.extract_tables(document_id, sync=True)

# New code - asynchronous extraction
task = client.parser.extract_tables(document_id, sync=False)
```

## Common Migration Issues

### Issue: AttributeError: 'SimbaClient' object has no attribute 'documents'

If you see this error, you need to update from the plural `documents` to the singular `document`:

```python
# Old
client.documents.create_from_file(...)

# New
client.document.create_from_file(...)
```

### Issue: TypeError: parse_document() got an unexpected keyword argument 'sync'

This means you're still using the old version of the SDK. Ensure you've installed the latest version:

```bash
pip install --upgrade simba-client
```

## Checking Your Version

You can check which version you're using:

```python
import simba_sdk
print(simba_sdk.__version__)
```

Versions 0.1.0 and higher are using the new `simba-client` package structure.

## Need Help?

If you encounter any issues during migration, please:

1. Check the [full documentation](https://simba-client.readthedocs.io)
2. Open an issue on our [GitHub repository](https://github.com/yourusername/simba-client/issues)
3. Contact support at support@example.com 