# Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using the Simba Client (formerly simba_sdk).

## Connection Issues

### Unable to Connect to the Simba Server

**Symptoms**:
- Connection timeouts
- `SimbaConnectionError` exceptions

**Possible Causes**:
1. Incorrect API URL
2. Server is down
3. Network issues
4. Firewall blocking requests

**Solutions**:
1. Verify the API URL is correct and includes the protocol (http:// or https://)
2. Check if the server is running by visiting the health check endpoint in a browser
3. Verify your network connection
4. Check your firewall settings to ensure it allows outbound connections to the server

```python
# Verify connection to the server
try:
    client = SimbaClient(api_url="https://your-server.example.com", api_key="your-key")
    is_healthy = client.health_check()
    print(f"Server is {'healthy' if is_healthy else 'unhealthy'}")
except SimbaConnectionError as e:
    print(f"Connection failed: {e}")
```

## Authentication Issues

### Invalid API Key

**Symptoms**:
- 401 Unauthorized errors
- `SimbaAPIError` with status code 401

**Solutions**:
1. Verify your API key is correct
2. Check if your API key has expired
3. Ensure you're using the correct API key for the environment (development vs. production)

```python
# Test authentication
try:
    client = SimbaClient(api_url="https://your-server.example.com", api_key="your-key")
    client.document_manager.list_documents(limit=1)
    print("Authentication successful")
except SimbaAPIError as e:
    if e.status_code == 401:
        print("Authentication failed: Invalid API key")
    else:
        print(f"API error: {e}")
```

## Document Upload Issues

### File Upload Failing

**Symptoms**:
- Upload fails with error messages
- Timeout during upload

**Possible Causes**:
1. File size exceeds server limits
2. Unsupported file format
3. Network interruption during upload

**Solutions**:
1. Check the file size and ensure it's within server limits (typically 10-50MB)
2. Verify the file format is supported (PDF, DOCX, etc.)
3. For large files, use a stable network connection

```python
# Check file size before upload
import os

def is_file_size_acceptable(file_path, max_size_mb=20):
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    return file_size_mb <= max_size_mb, file_size_mb

file_path = "large_document.pdf"
is_acceptable, size_mb = is_file_size_acceptable(file_path)
if not is_acceptable:
    print(f"File is too large ({size_mb:.2f}MB). Maximum size is 20MB.")
else:
    try:
        result = client.document_manager.upload_document(file_path)
        print(f"Upload successful. Document ID: {result['document_id']}")
    except Exception as e:
        print(f"Upload failed: {e}")
```

## Parsing Issues

### Parsing Task Failing

**Symptoms**:
- Parsing task status shows "FAILURE"
- Error messages in the task result

**Possible Causes**:
1. Document format issues
2. Document content not compatible with parser
3. Server-side parsing errors

**Solutions**:
1. Verify the document opens correctly in its native application
2. Try parsing with different document formats (e.g., convert DOCX to PDF)
3. Check server logs for detailed error information

```python
# Check parsing status with error handling
def check_parsing_status(client, task_id, max_attempts=10, delay_seconds=5):
    import time
    for attempt in range(max_attempts):
        try:
            status = client.parser_manager.get_parse_status(task_id)
            if status['state'] == 'SUCCESS':
                return status['result']
            elif status['state'] == 'FAILURE':
                print(f"Parsing failed: {status.get('error', 'Unknown error')}")
                return None
            print(f"Parsing in progress... ({attempt+1}/{max_attempts})")
            time.sleep(delay_seconds)
        except Exception as e:
            print(f"Error checking status: {e}")
            return None
    print("Parsing timed out")
    return None

# Usage
task_id = "your-task-id"
result = check_parsing_status(client, task_id)
if result:
    print("Parsing completed successfully")
```

### Synchronous Parsing Timeout

**Symptoms**:
- Request times out during synchronous parsing
- `SimbaConnectionError` with timeout message

**Solutions**:
1. Use asynchronous parsing for large documents
2. Increase the client timeout

```python
# Increase timeout for large documents
client = SimbaClient(
    api_url="https://your-server.example.com",
    api_key="your-key",
    timeout=300  # 5 minutes
)

# Or use asynchronous parsing
parse_result = client.parser_manager.parse_document(
    document_id="your-document-id",
    sync=False  # Use asynchronous parsing
)
print(f"Task ID: {parse_result['task_id']}")
```

## Import and Dependency Issues

### Module Import Errors

**Symptoms**:
- `ImportError` or `ModuleNotFoundError` exceptions

**Solutions**:
1. Verify the package is installed correctly
2. Check for version conflicts
3. Try reinstalling the package

```bash
# Reinstall the package
pip uninstall -y simba-client
pip install simba-client
```

If you're using a development version:

```bash
# Reinstall in development mode
pip uninstall -y simba-client
cd /path/to/simba-client
pip install -e .
```

## Version Compatibility

### API Version Mismatch

**Symptoms**:
- Unexpected API errors
- Missing or incorrect fields in responses

**Solutions**:
1. Check the client and server versions
2. Update the client to match the server version

```python
# Check client version
import simba_sdk
print(f"Client version: {simba_sdk.__version__}")

# Check server version
client = SimbaClient(api_url="https://your-server.example.com", api_key="your-key")
server_version = client.get_version()
print(f"Server version: {server_version}")
```

## Getting Help

If you still encounter issues after trying these troubleshooting steps:

1. Check the [full documentation](https://github.com/yourusername/simba-client/docs)
2. Search for similar issues in the [GitHub repository](https://github.com/yourusername/simba-client/issues)
3. Open a new issue with details about your problem:
   - Client version
   - Server version
   - Error messages
   - Steps to reproduce the issue
   - Sample code (with sensitive information removed)

For urgent issues, contact support at support@example.com. 