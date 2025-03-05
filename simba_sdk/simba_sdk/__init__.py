"""Simba SDK - Python client for Simba Knowledge Management System."""

from .client import SimbaClient
from .document import DocumentManager
from .parser import ParserManager

__version__ = "0.1.0"

# Make SimbaClient available at the package level
__all__ = ["SimbaClient", "DocumentManager", "ParserManager"]
