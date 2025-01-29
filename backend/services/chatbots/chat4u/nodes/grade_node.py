from ..chains.grade_chain import grade_chain
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
import time
from ..chains.grade_chain import GradeDocuments

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.RemoteProtocolError, httpx.ReadTimeout)),
    before_sleep=lambda _: logger.warning("Retrying document grading...")
)
def grade_document_with_retry(question, document_content):
    try:
        return grade_chain.invoke(
            {"question": question, "document": document_content}
        )
    except Exception as e:
        logger.error(f"Grading failed: {str(e)}")
        return GradeDocuments(binary_score="no")

def grade(state):
    """
    Grade documents with enhanced connection handling

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, grade, that contains grade
    """

    logger.info("---DOCUMENT RELEVANCE CHECK---")
    question = state["question"]
    documents = state["documents"]

    filtered_docs = []

    client_params = {
        "timeout": 30.0,
        "limits": httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20,
            keepalive_expiry=60
        ),
        "transport": httpx.HTTPTransport(retries=3),
        "headers": {"Content-Type": "application/json"}
    }

    try:
        with httpx.Client(**client_params) as client:
            for idx, d in enumerate(documents):
                try:
                    if idx > 0:
                        time.sleep(1.0)
                        
                    score = grade_document_with_retry(question, d.page_content)
                    
                    if score.binary_score == "yes":
                        logger.info(f"Document {d.id[:8]} relevant")
                        filtered_docs.append(d)
                    else:
                        logger.warning(f"Document {d.id[:8]} not relevant")
                        
                except Exception as doc_error:
                    logger.error(f"Error grading document {d.id[:8]}: {str(doc_error)}")
                    continue

        return {"documents": filtered_docs, "question": question}

    except httpx.RemoteProtocolError as e:
        logger.error(f"Connection error: {str(e)}")
        return {"documents": [], "question": question}
        
    except Exception as e:
        logger.critical(f"Critical grading error: {str(e)}")
        raise