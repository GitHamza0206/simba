# Installation Guide

This guide covers the different ways to install the Simba Client (formerly simba_sdk).

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installing from PyPI

The easiest way to install the Simba Client is from PyPI using pip:

```bash
pip install simba-client
```

This will install the latest stable release of the client along with all its dependencies.

## Installing a Specific Version

To install a specific version:

```bash
pip install simba-client==0.1.0
```

## Development Installation

If you're contributing to the development of the Simba Client, or want to use the latest code from the repository:

### Using Poetry (Recommended)

1. First, make sure you have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository:

```bash
git clone https://github.com/yourusername/simba-client.git
cd simba-client
```

3. Install the package and its dependencies:

```bash
poetry install
```

This will create a virtual environment and install all dependencies, including development dependencies.

4. Activate the virtual environment:

```bash
poetry shell
```

### Using pip

If you prefer not to use Poetry, you can still install the package for development using pip:

```bash
git clone https://github.com/yourusername/simba-client.git
cd simba-client
pip install -e .
```

## Verifying Installation

You can verify that the installation was successful by checking the version:

```python
import simba_sdk
print(simba_sdk.__version__)
```

Or by running a simple example:

```python
from simba_sdk import SimbaClient

# Initialize the client (will raise an error if not installed correctly)
client = SimbaClient(api_url="https://api.example.com", api_key="your-api-key")
print("Simba Client initialized successfully!")
```

## Dependencies

The Simba Client depends on the following libraries:

- `requests`: For HTTP communication with the API
- `urllib3`: Used by requests for HTTP operations
- `pydantic`: For data validation and settings management

These dependencies will be installed automatically when you install the package.

## Server Requirements

Note that the Simba Client is a client library that needs to connect to a Simba server. You'll need:

1. The URL of a running Simba server (either self-hosted or hosted by a service provider)
2. A valid API key for that server

Contact your system administrator for these details if you're using an existing Simba installation.

## Troubleshooting

### Common Installation Issues

#### ImportError: No module named 'simba_sdk'

This usually means the package wasn't installed correctly. Try reinstalling:

```bash
pip uninstall simba-client
pip install simba-client
```

#### VersionConflict

If you encounter version conflicts with other packages, you might need to create a virtual environment:

```bash
python -m venv simba-env
source simba-env/bin/activate  # On Windows: simba-env\Scripts\activate
pip install simba-client
```

#### SSL Certificate Errors

If you encounter SSL certificate errors when connecting to the API, you might need to install or update certificates:

```bash
pip install --upgrade certifi
```

For more help, please refer to our [troubleshooting guide](./troubleshooting.md) or [open an issue](https://github.com/yourusername/simba-client/issues). 