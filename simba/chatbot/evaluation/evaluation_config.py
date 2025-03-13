import os
from langfuse import Langfuse
from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextPrecisionWithoutReference
from ragas.run_config import RunConfig
from ragas.metrics.base import MetricWithLLM, MetricWithEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_langfuse_client():
    """Initialize and return a Langfuse client."""
    langfuse = Langfuse()
    langfuse.auth_check()
    return langfuse

def get_ragas_metrics():
    """Return a list of initialized Ragas metrics."""
    # Define metrics to evaluate
    metrics = [
        Faithfulness(),
        ResponseRelevancy(),
        LLMContextPrecisionWithoutReference(),
    ]
    
    # Create LLM and embeddings wrappers (using Langchain)
    llm = ChatOpenAI()  # add model parameters if needed
    emb = OpenAIEmbeddings()
    
    # Initialize each metric with the LLM and embeddings
    for metric in metrics:
        if isinstance(metric, MetricWithLLM):
            metric.llm = LangchainLLMWrapper(llm)
        if isinstance(metric, MetricWithEmbeddings):
            metric.embeddings = LangchainEmbeddingsWrapper(emb)
        metric.init(RunConfig())
        
    return metrics
