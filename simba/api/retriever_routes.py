import uuid
from typing import List, Optional

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
    score_threshold: Optional[float] = 0
    filter: Optional[dict] = None


class RetrieveResponse(BaseModel):
    documents: List[Document]


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
