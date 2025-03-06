from langfuse.callback import CallbackHandler
import os
from langfuse import Langfuse

def get_langfuse_client():
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY") or not os.getenv("LANGFUSE_HOST"):
        return None
    
    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"))

# Initialize the Langfuse callback handler
def get_langfuse_callback_handler():
    """
    Initialize and return a Langfuse callback handler for tracing and evaluation.
    
    Returns:
        CallbackHandler: Configured Langfuse callback handler
    """
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY") or not os.getenv("LANGFUSE_HOST"):
        return None
    
    langfuse_handler = CallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )
    return langfuse_handler 