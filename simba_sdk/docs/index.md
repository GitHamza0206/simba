# Simba Client Documentation

Welcome to the Simba Client documentation. This SDK provides a Python interface for interacting with the Simba document processing API.

## Features

- **Document Management**: Upload, download, list, and delete documents
- **Document Parsing**: Extract structured data from documents, including tables, forms, and entities
- **Document Embeddings**: Generate vector embeddings for documents to enable semantic search and similarity analysis
- **Authentication**: Secure API access with API keys
- **Error Handling**: Robust error handling for API requests

## Getting Started

- [Installation Guide](installation.md): Install the Simba Client package
- [Quick Start Guide](quickstart.md): Quickly get up and running with the SDK
- [Migration Guide](migration.md): Transition from simba_sdk to simba-client

## Core Functionality

- [Document Management](document_management.md): Work with document uploads and management
- [Document Parsing](document_parsing.md): Extract structured data from documents
- [Synchronous Parsing](synchronous_parsing.md): Parse documents synchronously
- [Document Embeddings](embeddings.md): Generate and manage document embeddings for semantic search

## Reference

- [API Reference](api_reference.md): Detailed information about classes and methods
- [Examples](../examples/): Code examples for common tasks
- [Troubleshooting](troubleshooting.md): Solutions for common issues

## Development

- [Contributing Guidelines](contributing.md): How to contribute to the SDK
- [Testing](testing.md): How to run tests for the SDK
- [Release Notes](release_notes.md): What's new in each version

## Table of Contents

### Getting Started
- [Installation Guide](./installation.md)
- [Quick Start Tutorial](./quickstart.md)
- [Migration from simba_sdk](./migration.md)

### Core Concepts
- [API Reference](./api_reference.md)
- [Document Management](./document_management.md)
- [Synchronous Parsing](./synchronous_parsing.md)
- [Asynchronous Parsing](./async_parsing.md)

### Advanced Topics
- [Error Handling](./error_handling.md)
- [Authentication](./authentication.md)
- [Batch Processing](./batch_processing.md)
- [Performance Optimization](./performance.md)

### Troubleshooting
- [Troubleshooting Guide](./troubleshooting.md)
- [FAQs](./faqs.md)

### Development
- [Contributing](./contributing.md)
- [Development Setup](./development.md)
- [Testing](./testing.md)
- [Code Style](./code_style.md)

## What is Simba?

Simba is a powerful document processing platform that extracts structured data from unstructured documents. The Simba Client provides a convenient Python interface to the Simba API, allowing you to:

- Upload and manage documents
- Parse documents to extract text, tables, entities, and form data
- Process documents both synchronously and asynchronously
- Retrieve and manage parsing results

## Key Features

- **Document Management**: Upload, download, list, and delete documents
- **Flexible Parsing**: Extract valuable information from documents
- **Synchronous & Asynchronous Processing**: Choose the processing mode that fits your needs
- **Error Handling**: Robust error handling and reporting
- **Type Annotations**: Full Python type hints for better IDE integration

## System Requirements

- Python 3.8 or higher
- A valid API key for a Simba server
- Internet connection to communicate with the API

## Where to Go Next

If you're new to the Simba Client, we recommend starting with the [Installation Guide](./installation.md) followed by the [Quick Start Tutorial](./quickstart.md).

If you're migrating from the older `simba_sdk` package to the new `simba-client` package, check out the [Migration Guide](./migration.md).

## Getting Help

If you encounter any issues or have questions:

1. Check the [Troubleshooting Guide](./troubleshooting.md)
2. Search or ask in our [GitHub Issues](https://github.com/yourusername/simba-client/issues)
3. Contact support at support@example.com

## License

The Simba Client is licensed under the MIT License. See the LICENSE file for details. 