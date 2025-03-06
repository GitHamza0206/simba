"""
Utilities for evaluating RAG chains with RAGAS and logging results to Langfuse.
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Union

from langchain.schema import Document
from langfuse import Langfuse

from simba.chatbot.demo.graph import graph
from simba.chatbot.evaluation.ragas_evaluator import RAGASEvaluator
from simba.core.langfuse_config import get_langfuse_client


def evaluate_rag_result(
    question: str,
    retrieved_docs: List[Union[str, Document]],
    answer: str,
    trace_id: Optional[str] = None,
    evaluator_model: str = "gpt-4"
) -> Dict[str, float]:
    """
    Evaluate a RAG result using RAGAS metrics and log to Langfuse.
    
    Args:
        question: The user's question
        retrieved_docs: The retrieved documents (can be Document objects or strings)
        answer: The generated answer
        trace_id: Optional Langfuse trace ID to log results to
        evaluator_model: Model to use for RAGAS evaluation
        
    Returns:
        Dictionary of evaluation scores
    """
    # Initialize the RAGAS evaluator
    evaluator = RAGASEvaluator(evaluator_model=evaluator_model)
    
    # If no documents were retrieved, use a placeholder
    if not retrieved_docs:
        retrieved_docs = ["No documents were retrieved for this query."]
    
    # Create a sample for evaluation
    sample = evaluator.create_sample(
        user_question=question,
        retrieved_docs=retrieved_docs,
        model_answer=answer
    )
    
    try:
        # Run evaluation
        scores = asyncio.run(
            evaluator.evaluate_sample(sample=sample, trace_id=trace_id)
        )
        return scores
    except Exception as e:
        print(f"Error during RAGAS evaluation: {str(e)}")
        # Return empty scores if evaluation fails
        return {}


def evaluate_graph_result(
    result: Dict[str, Any],
    trace_id: Optional[str] = None,
    evaluator_model: str = "gpt-4"
) -> Dict[str, float]:
    """
    Evaluate a result from the LangGraph RAG chain using RAGAS.
    
    Args:
        result: The output from graph.invoke()
        trace_id: Optional Langfuse trace ID to log results to
        evaluator_model: Model to use for RAGAS evaluation
        
    Returns:
        Dictionary of evaluation scores
    """
    # Extract information from the graph result
    if "messages" in result and len(result["messages"]) >= 2:
        question = result["messages"][-2].content  # User's question
        answer = result["messages"][-1].content    # Model's answer
    else:
        return {}  # Can't evaluate without messages
    
    # Get documents if available
    documents = result.get("documents", [])
    
    # Run evaluation
    return evaluate_rag_result(
        question=question,
        retrieved_docs=documents,
        answer=answer,
        trace_id=trace_id,
        evaluator_model=evaluator_model
    )


def run_graph_with_evaluation(
    user_question: str,
    trace_name: str = "RAG query with evaluation"
) -> Dict[str, Any]:
    """
    Run the LangGraph RAG chain with RAGAS evaluation.
    
    Args:
        user_question: The user's question
        trace_name: Name for the Langfuse trace
        
    Returns:
        Dictionary with RAG results and evaluation scores
    """
    # Initialize Langfuse client
    langfuse = get_langfuse_client()
    
    # Start a new trace
    trace = None
    trace_id = None
    if langfuse:
        trace = langfuse.trace(name=trace_name)
        trace_id = trace.id
    
    # Create a span for the graph execution
    graph_span = None
    if trace:
        graph_span = trace.span(
            name="rag_chain",
            input={"question": user_question}
        )
    
    # Run the graph
    answer = None
    documents = []
    result = {}
    
    try:
        # Prepare input for the graph
        graph_input = {"messages": [{"role": "user", "content": user_question}]}
        
        # Generate a unique thread ID for the checkpointer
        thread_id = str(uuid.uuid4())
        
        # Run the graph with proper checkpointer configuration
        result = graph.invoke(
            graph_input,
            config={"configurable": {"thread_id": thread_id}}
        )
        
        # Extract answer and documents
        if "messages" in result and len(result["messages"]) > 0:
            answer = result["messages"][-1].content
        documents = result.get("documents", [])
        
        # End the graph span if we have one
        if trace and graph_span:
            graph_span.end(output={
                "answer": answer,
                "num_documents": len(documents)
            })
    except Exception as e:
        if trace and graph_span:
            graph_span.end(error={"message": str(e)})
        if trace:
            try:
                trace.update(status="error", error={"message": str(e)})
            except:
                pass  # Ignore errors in trace updating
        raise
    
    # Create a span for the evaluation
    eval_span = None
    if trace:
        eval_span = trace.span(
            name="evaluation",
            input={
                "question": user_question,
                "answer": answer,
                "num_documents": len(documents)
            }
        )
    
    # Run evaluation
    scores = {}
    try:
        scores = evaluate_graph_result(result, trace_id)
        
        # End the evaluation span if we have one
        if trace and eval_span:
            eval_span.end(output={"scores": scores})
    except Exception as e:
        if trace and eval_span:
            eval_span.end(error={"message": str(e)})
    
    # End the trace if it has the end method
    if trace:
        try:
            trace.update(status="success")
        except:
            pass  # Ignore errors in trace updating
    
    # Return results and scores
    return {
        "question": user_question,
        "answer": answer,
        "documents": documents,
        "scores": scores,
        "trace_id": trace_id
    }


def batch_evaluate_samples(samples: List[Dict]) -> Dict:
    """
    Run batch RAGAS evaluation on a list of samples.
    
    Args:
        samples: List of dictionaries with keys 'question', 'contexts', 'answer'
        
    Returns:
        Dictionary of evaluation results
    """
    # Validate samples
    for i, sample in enumerate(samples):
        if "question" not in sample or "answer" not in sample:
            print(f"Warning: Sample at index {i} is missing required fields")
            continue
        
        # Ensure contexts exist
        if "contexts" not in sample or not sample["contexts"]:
            samples[i]["contexts"] = ["No context provided for this query."]
    
    # Initialize evaluator and run batch evaluation
    try:
        evaluator = RAGASEvaluator()
        return evaluator.batch_evaluate(samples)
    except Exception as e:
        print(f"Error in batch evaluation: {str(e)}")
        return {} 