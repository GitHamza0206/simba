# Re-export the SimbaClient class from the nested module
from simba_sdk.simba_sdk.client import SimbaClient
from simba_sdk.simba_sdk.document import DocumentManager

# Make these classes available at the package level
__all__ = ["SimbaClient", "DocumentManager"]