"""Simba SDK - Python client for Simba Knowledge Management System."""

from .client import SimbaClient
from .document import DocumentManager
from .parser import ParserManager
from .embed import EmbeddingManager
from .retrieve import RetrieveManager
from .auth import AuthManager

__version__ = "0.1.0"

# Make SimbaClient available at the package level
__all__ = ["SimbaClient", "DocumentManager", "ParserManager", "EmbeddingManager", "RetrieveManager", "AuthManager"]
