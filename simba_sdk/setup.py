#!/usr/bin/env python
"""
Compatibility setup.py for non-Poetry users.
We recommend using Poetry for installation, but this file is provided for compatibility.
"""

import re
from setuptools import setup, find_packages

# Read version from __init__.py
with open("simba_sdk/__init__.py", "r") as f:
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', f.read())
    version = version_match.group(1) if version_match else "0.1.0"

# Read README.md for long description
with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="simba-client",
    version=version,
    description="Python client for the Simba document processing API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Simba Team",
    author_email="info@example.com",
    url="https://github.com/yourusername/simba-client",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "urllib3>=2.0.0",
        "pydantic>=2.0.0",
    ],
    project_urls={
        "Documentation": "https://simba-client.readthedocs.io",
        "Source": "https://github.com/yourusername/simba-client",
        "Bug Tracker": "https://github.com/yourusername/simba-client/issues",
    },
) 