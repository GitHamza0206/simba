"""Evals routes for customer service quality evaluation."""

import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from simba.core.config import settings
from simba.models import EvalItem, get_db
from simba.services import qdrant_service, retrieval_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evals")


class SourceInfo(BaseModel):
    document_id: str
    document_name: str
    chunk_text: str
    score: float


class EvalItemResponse(BaseModel):
    id: str
    question: str
    response: str | None
    sources: list[str] | None
    sources_groundtruth: list[str] | None
    comment: str | None
    latency_ms: float | None
    conversation_id: str | None
    conversation_history: str | None
    answer_groundtruth: str | None
    retrieval_precision: float | None
    retrieval_recall: float | None
    relevance_score: float | None
    faithfulness_score: float | None
    passed: bool | None
    error_category: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class EvalItemCreate(BaseModel):
    question: str
    response: str | None = None
    sources: list[str] | None = None
    sources_groundtruth: list[str] | None = None
    answer_groundtruth: str | None = None
    comment: str | None = None
    latency_ms: float | None = None
    conversation_id: str | None = None
    conversation_history: str | None = None


class EvalItemUpdate(BaseModel):
    comment: str | None = None
    sources_groundtruth: list[str] | None = None
    answer_groundtruth: str | None = None
    error_category: str | None = None


class EvalListResponse(BaseModel):
    items: list[EvalItemResponse]
    total: int


class GenerateQuestionsRequest(BaseModel):
    collection_name: str = "default"
    num_questions: int = 5


class GeneratedQuestion(BaseModel):
    question: str
    source_documents: list[str]
    answer_groundtruth: str


class GenerateQuestionsResponse(BaseModel):
    questions: list[GeneratedQuestion]


class RunEvalRequest(BaseModel):
    eval_id: str
    collection_name: str = "default"


class RunAllEvalsRequest(BaseModel):
    collection_name: str = "default"


class RunAllEvalsResponse(BaseModel):
    total: int
    completed: int
    failed: int
    results: list[EvalItemResponse]


def _eval_to_response(item: EvalItem) -> EvalItemResponse:
    return EvalItemResponse(
        id=item.id,
        question=item.question,
        response=item.response,
        sources=item.sources,
        sources_groundtruth=item.sources_groundtruth,
        comment=item.comment,
        latency_ms=item.latency_ms,
        conversation_id=item.conversation_id,
        conversation_history=item.conversation_history,
        answer_groundtruth=item.answer_groundtruth,
        retrieval_precision=item.retrieval_precision,
        retrieval_recall=item.retrieval_recall,
        relevance_score=item.relevance_score,
        faithfulness_score=item.faithfulness_score,
        passed=item.passed,
        error_category=item.error_category,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


def _calculate_retrieval_metrics(
    sources: list[str] | None, groundtruth: list[str] | None
) -> tuple[float | None, float | None]:
    if not sources or not groundtruth:
        return None, None

    source_names = {s.split(" (")[0] for s in sources}
    groundtruth_set = set(groundtruth)

    correct = len(source_names & groundtruth_set)
    precision = correct / len(source_names) if source_names else None
    recall = correct / len(groundtruth_set) if groundtruth_set else None
    return precision, recall


@router.get("", response_model=EvalListResponse)
async def list_evals(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all evaluation items."""
    query = db.query(EvalItem).order_by(desc(EvalItem.created_at))
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return EvalListResponse(
        items=[_eval_to_response(item) for item in items],
        total=total,
    )


@router.post("", response_model=EvalItemResponse)
async def create_eval(
    data: EvalItemCreate,
    db: Session = Depends(get_db),
):
    """Create a new evaluation item."""
    eval_item = EvalItem(
        id=str(uuid4()),
        question=data.question,
        response=data.response,
        sources=data.sources,
        sources_groundtruth=data.sources_groundtruth,
        answer_groundtruth=data.answer_groundtruth,
        comment=data.comment,
        latency_ms=data.latency_ms,
        conversation_id=data.conversation_id,
        conversation_history=data.conversation_history,
    )
    db.add(eval_item)
    db.commit()
    db.refresh(eval_item)

    return _eval_to_response(eval_item)


@router.get("/{eval_id}", response_model=EvalItemResponse)
async def get_eval(
    eval_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific evaluation item."""
    eval_item = db.query(EvalItem).filter(EvalItem.id == eval_id).first()
    if not eval_item:
        raise HTTPException(status_code=404, detail="Eval item not found")

    return _eval_to_response(eval_item)


@router.patch("/{eval_id}", response_model=EvalItemResponse)
async def update_eval(
    eval_id: str,
    data: EvalItemUpdate,
    db: Session = Depends(get_db),
):
    """Update an evaluation item (comment or groundtruth sources)."""
    eval_item = db.query(EvalItem).filter(EvalItem.id == eval_id).first()
    if not eval_item:
        raise HTTPException(status_code=404, detail="Eval item not found")

    if data.comment is not None:
        eval_item.comment = data.comment
    if data.sources_groundtruth is not None:
        eval_item.sources_groundtruth = data.sources_groundtruth
    if data.answer_groundtruth is not None:
        eval_item.answer_groundtruth = data.answer_groundtruth
    if data.error_category is not None:
        eval_item.error_category = data.error_category

    db.commit()
    db.refresh(eval_item)

    return _eval_to_response(eval_item)


@router.delete("/{eval_id}")
async def delete_eval(
    eval_id: str,
    db: Session = Depends(get_db),
):
    """Delete an evaluation item."""
    eval_item = db.query(EvalItem).filter(EvalItem.id == eval_id).first()
    if not eval_item:
        raise HTTPException(status_code=404, detail="Eval item not found")

    db.delete(eval_item)
    db.commit()

    return {"message": "Eval item deleted"}


@router.post("/generate", response_model=GenerateQuestionsResponse)
async def generate_questions(
    data: GenerateQuestionsRequest,
):
    """Generate evaluation questions from documents using LLM.

    This endpoint samples chunks from documents in the collection and uses
    an LLM to generate diverse customer service questions based on the content.
    """
    try:
        from qdrant_client.http.exceptions import UnexpectedResponse

        client = qdrant_service.get_qdrant_client()

        try:
            results, _ = client.scroll(
                collection_name=data.collection_name,
                limit=50,
                with_payload=True,
                with_vectors=False,
            )
        except UnexpectedResponse:
            return GenerateQuestionsResponse(questions=[])

        if not results:
            return GenerateQuestionsResponse(questions=[])

        doc_chunks: dict[str, list[dict]] = {}
        for point in results:
            doc_name = point.payload.get("document_name", "unknown")
            chunk_text = point.payload.get("chunk_text", "")
            if doc_name not in doc_chunks:
                doc_chunks[doc_name] = []
            doc_chunks[doc_name].append(
                {
                    "text": chunk_text,
                    "position": point.payload.get("chunk_position", 0),
                }
            )

        context_parts = []
        for doc_name, chunks in doc_chunks.items():
            sorted_chunks = sorted(chunks, key=lambda x: x["position"])[:3]
            doc_content = "\n".join([c["text"] for c in sorted_chunks])
            context_parts.append(f"=== Document: {doc_name} ===\n{doc_content}")

        context = "\n\n".join(context_parts)

        llm = init_chat_model(model=settings.llm_model, temperature=0.7)

        prompt = f"""Based on the following document excerpts from a knowledge base, generate {data.num_questions} diverse customer service questions that real users might ask about this content.

The questions should:
1. Be specific and answerable from the provided documents
2. Cover different topics/documents when possible
3. Represent realistic customer queries
4. Include a mix of simple factual questions and more complex ones

Documents:
{context}

Generate exactly {data.num_questions} questions. For each question:
1. Identify which document(s) would be the primary source for answering it
2. Provide the ideal/expected answer based on the document content (this will be used as ground truth for evaluation)

Return your response as a JSON array with objects containing "question", "source_documents", and "answer_groundtruth" fields.

Example format:
[
  {{"question": "What is your return policy for electronics?", "source_documents": ["returns-policy.pdf"], "answer_groundtruth": "Electronics can be returned within 30 days of purchase with original receipt and packaging."}},
  {{"question": "How long does shipping take?", "source_documents": ["shipping-guide.pdf", "faq.pdf"], "answer_groundtruth": "Standard shipping takes 5-7 business days, while express shipping takes 2-3 business days."}}
]

Return ONLY the JSON array, no other text."""

        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            if content.startswith("json"):
                content = content[4:].strip()

        questions_data = json.loads(content)

        questions = [
            GeneratedQuestion(
                question=q["question"],
                source_documents=q.get("source_documents", list(doc_chunks.keys())),
                answer_groundtruth=q.get("answer_groundtruth", ""),
            )
            for q in questions_data
        ]

        return GenerateQuestionsResponse(questions=questions)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse generated questions")
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_eval(
    data: RunEvalRequest,
    db: Session = Depends(get_db),
):
    """Run evaluation on a single eval item - retrieves answer and sources."""
    eval_item = db.query(EvalItem).filter(EvalItem.id == data.eval_id).first()
    if not eval_item:
        raise HTTPException(status_code=404, detail="Eval item not found")

    try:
        chunks, latency = retrieval_service.retrieve(
            query=eval_item.question,
            collection_name=data.collection_name,
            limit=5,
            return_latency=True,
        )

        sources = [f"{chunk.document_name} (score: {chunk.score:.2f})" for chunk in chunks]

        context = "\n\n".join([chunk.chunk_text for chunk in chunks])

        llm = init_chat_model(model=settings.llm_model, temperature=0)

        prompt = f"""You are a helpful customer service assistant. Answer the following question based on the provided context.

Context:
{context}

Question: {eval_item.question}

Provide a helpful and accurate response based on the context. If the context doesn't contain relevant information, say so."""

        import time

        start = time.perf_counter()
        response = await llm.ainvoke(prompt)
        generation_time = (time.perf_counter() - start) * 1000

        total_latency = latency.get("total_ms", 0) + generation_time

        eval_item.response = response.content
        eval_item.sources = sources
        eval_item.latency_ms = total_latency

        precision, recall = _calculate_retrieval_metrics(sources, eval_item.sources_groundtruth)
        eval_item.retrieval_precision = precision
        eval_item.retrieval_recall = recall

        relevance, faithfulness = await _score_response(
            llm, eval_item.question, response.content, context
        )
        eval_item.relevance_score = relevance
        eval_item.faithfulness_score = faithfulness

        eval_item.passed = _determine_pass(precision, recall, relevance, faithfulness)

        db.commit()
        db.refresh(eval_item)

        return _eval_to_response(eval_item)

    except Exception as e:
        logger.error(f"Error running eval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _score_response(llm, question: str, response: str, context: str) -> tuple[float, float]:
    scoring_prompt = f"""You are evaluating a customer service response. Score the following on a scale of 0.0 to 1.0.

Question: {question}

Context provided to agent:
{context}

Agent's response:
{response}

Evaluate:
1. Relevance: How relevant is the response to the question? (0.0 = completely irrelevant, 1.0 = perfectly relevant)
2. Faithfulness: Is the response grounded in the provided context? (0.0 = contains hallucinations/unsupported claims, 1.0 = fully supported by context)

Return ONLY a JSON object with "relevance" and "faithfulness" as numbers between 0.0 and 1.0.
Example: {{"relevance": 0.85, "faithfulness": 0.9}}"""

    try:
        score_response = await llm.ainvoke(scoring_prompt)
        content = score_response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            if content.startswith("json"):
                content = content[4:].strip()
        scores = json.loads(content)
        return float(scores.get("relevance", 0)), float(scores.get("faithfulness", 0))
    except Exception as e:
        logger.warning(f"Failed to score response: {e}")
        return 0.0, 0.0


def _determine_pass(
    precision: float | None,
    recall: float | None,
    relevance: float | None,
    faithfulness: float | None,
) -> bool:
    if relevance is not None and relevance < 0.5:
        return False
    if faithfulness is not None and faithfulness < 0.5:
        return False
    if recall is not None and recall < 0.3:
        return False
    return True


@router.post("/run-all", response_model=RunAllEvalsResponse)
async def run_all_evals(
    data: RunAllEvalsRequest,
    db: Session = Depends(get_db),
):
    """Run evaluation on all eval items that don't have responses yet."""
    evals_to_run = db.query(EvalItem).filter(EvalItem.response.is_(None)).all()

    results = []
    completed = 0
    failed = 0

    for eval_item in evals_to_run:
        try:
            chunks, latency = retrieval_service.retrieve(
                query=eval_item.question,
                collection_name=data.collection_name,
                limit=5,
                return_latency=True,
            )

            sources = [f"{chunk.document_name} (score: {chunk.score:.2f})" for chunk in chunks]
            context = "\n\n".join([chunk.chunk_text for chunk in chunks])

            llm = init_chat_model(model=settings.llm_model, temperature=0)

            prompt = f"""You are a helpful customer service assistant. Answer the following question based on the provided context.

Context:
{context}

Question: {eval_item.question}

Provide a helpful and accurate response based on the context. If the context doesn't contain relevant information, say so."""

            import time

            start = time.perf_counter()
            response = await llm.ainvoke(prompt)
            generation_time = (time.perf_counter() - start) * 1000

            total_latency = latency.get("total_ms", 0) + generation_time

            eval_item.response = response.content
            eval_item.sources = sources
            eval_item.latency_ms = total_latency

            precision, recall = _calculate_retrieval_metrics(sources, eval_item.sources_groundtruth)
            eval_item.retrieval_precision = precision
            eval_item.retrieval_recall = recall

            relevance, faithfulness = await _score_response(
                llm, eval_item.question, response.content, context
            )
            eval_item.relevance_score = relevance
            eval_item.faithfulness_score = faithfulness

            eval_item.passed = _determine_pass(precision, recall, relevance, faithfulness)

            db.commit()
            db.refresh(eval_item)

            results.append(_eval_to_response(eval_item))
            completed += 1

        except Exception as e:
            logger.error(f"Error running eval {eval_item.id}: {e}")
            failed += 1

    return RunAllEvalsResponse(
        total=len(evals_to_run),
        completed=completed,
        failed=failed,
        results=results,
    )
