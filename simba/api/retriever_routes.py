import uuid
from typing import List, Optional, Dict

from fastapi import APIRouter, Body
from langchain.schema import Document
from pydantic import BaseModel

from simba.models.simbadoc import MetadataType, SimbaDoc
from simba.retrieval import RetrievalMethod, Retriever

retriever_route = APIRouter(prefix="/retriever", tags=["Retriever"])
retriever = Retriever()


class RetrieveRequest(BaseModel):
    query: str
    method: Optional[str] = "default"
    k: Optional[int] = 5
    score_threshold: Optional[float] = None
    filter: Optional[dict] = None


class RetrieveResponse(BaseModel):
    documents: List[Document]


class RetrievalStrategyInfo(BaseModel):
    name: str
    description: str


class RetrievalStrategiesResponse(BaseModel):
    strategies: Dict[str, str]


@retriever_route.post("/retrieve")
async def retrieve_documents(request: RetrieveRequest) -> RetrieveResponse:
    """
    Retrieve documents using the specified method.

    Args:
        request: RetrieveRequest with query and retrieval parameters

    Returns:
        List of retrieved documents as SimbaDoc objects
    """
    documents = retriever.retrieve(
        query=request.query,
        method=request.method,
        k=request.k,
        score_threshold=request.score_threshold,
        filter=request.filter,
    )

    return RetrieveResponse(documents=documents)


@retriever_route.get("/strategies")
async def get_retrieval_strategies() -> RetrievalStrategiesResponse:
    """
    Get all available retrieval strategies.

    Returns:
        Dictionary of available retrieval strategies with descriptions
    """
    strategy_descriptions = {
        RetrievalMethod.DEFAULT.value: "Default retrieval strategy that balances relevance and performance",
        RetrievalMethod.SEMANTIC.value: "Semantic search using vector embeddings for meaning-based retrieval",
        RetrievalMethod.KEYWORD.value: "Keyword-based search using traditional text matching techniques",
        RetrievalMethod.HYBRID.value: "Hybrid search combining semantic and keyword approaches",
        RetrievalMethod.ENSEMBLE.value: "Ensemble search that combines multiple retrieval strategies with weights",
        RetrievalMethod.RERANKED.value: "Semantic search followed by reranking for improved relevance",
    }
    
    return RetrievalStrategiesResponse(strategies=strategy_descriptions)