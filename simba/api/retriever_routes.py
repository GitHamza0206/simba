from fastapi import APIRouter, Body
from typing import List, Optional
import uuid

from simba.retrieval import Retriever, RetrievalMethod
from simba.models.simbadoc import SimbaDoc, MetadataType
from pydantic import BaseModel
from langchain.schema import Document

retriever_route = APIRouter(prefix="/retriever", tags=["Retriever"])
retriever = Retriever()


class RetrieveRequest(BaseModel):
    query: str
    method: Optional[str] = "default"
    k: Optional[int] = 5
    score_threshold: Optional[float] = None
    filter: Optional[dict] = None


class RetrieveResponse(BaseModel):
    documents: List[SimbaDoc]


@retriever_route.get("/as_retriever")
async def get_retriever():
    return retriever.as_retriever()  # TODO: Add config in /dto/retriever_dto.py


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
        filter=request.filter
    )
    
    # Convert documents to SimbaDoc objects
    simba_docs = []
    for i, doc in enumerate(documents):
        # Extract metadata or create default
        meta_dict = doc.metadata if hasattr(doc, "metadata") and doc.metadata else {}
        
        # Create metadata
        metadata = MetadataType(
            filename=meta_dict.get("filename", f"result_{i}"),
            type=meta_dict.get("type", "retrieval_result"),
            chunk_number=meta_dict.get("chunk_number", i),
            page_number=meta_dict.get("page_number", 0),
            enabled=True,
            parsing_status="completed",
            size=meta_dict.get("size", "unknown"),
            loader=meta_dict.get("loader", "retriever"),
            parser=meta_dict.get("parser", None),
            splitter=meta_dict.get("splitter", None),
            uploadedAt=meta_dict.get("uploadedAt", ""),
            file_path=meta_dict.get("file_path", ""),
            parsed_at=meta_dict.get("parsed_at", "")
        )
        
        # Create SimbaDoc
        simba_doc = SimbaDoc(
            id=str(uuid.uuid4()),
            documents=[doc],
            metadata=metadata
        )
        
        simba_docs.append(simba_doc)
    
    return RetrieveResponse(documents=simba_docs)
