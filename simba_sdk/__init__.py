"""
Simba Client - Python SDK for interacting with the Simba document processing API.
"""

__version__ = "0.1.0"
__author__ = "Simba Team"
__license__ = "MIT"

# Re-export the SimbaClient class from the nested module
from simba_sdk.simba_sdk.client import SimbaClient
from simba_sdk.simba_sdk.document import DocumentManager
from simba_sdk.simba_sdk.parser import ParserManager
from simba_sdk.simba_sdk.embed import EmbeddingManager
from simba_sdk.simba_sdk.retrieve import RetrieveManager

# Make these classes available at the package level
__all__ = ["SimbaClient", "DocumentManager", "ParserManager", "EmbeddingManager", "RetrieveManager"]

# Alias for backward compatibility if someone imports from simba_client
# This will help with transitioning to the new package name
SimbaClient = SimbaClient
DocumentManager = DocumentManager
ParserManager = ParserManager
EmbeddingManager = EmbeddingManager
RetrieveManager = RetrieveManager