from ..chains.generate_chain import generate_chain
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.RemoteProtocolError, httpx.ReadTimeout)),
    before_sleep=lambda _: logger.warning("Retrying due to connection error...")
)
def generate_with_retry(context, question):
    return generate_chain.invoke({"context": context, "question": question})

def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    try:
        # Configure timeout and connection limits
        client_params = {
            "timeout": 30.0,
            "limits": httpx.Limits(max_keepalive_connections=5, max_connections=10)
        }
        
        # RAG generation with retry and proper connection management
        with httpx.Client(**client_params) as client:
            generation = generate_with_retry(
                context=documents,
                question=question
            )
            
        return {"documents": documents, "question": question, "generation": generation}

    except httpx.RemoteProtocolError as e:
        logger.error(f"Connection protocol error: {str(e)}")
        raise RuntimeError("Failed to generate response due to connection issues") from e
        
    except httpx.ReadTimeout as e:
        logger.error(f"Request timed out: {str(e)}")
        raise TimeoutError("Response generation timed out") from e
        
    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}")
        raise