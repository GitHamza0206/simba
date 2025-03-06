"""
Example script demonstrating how to evaluate the LangGraph RAG chain using RAGAS
and logging results to Langfuse.
"""
import asyncio
import json
import time
import uuid
from pprint import pprint

from simba.chatbot.demo.graph import graph
from simba.chatbot.evaluation.rag_evaluation import (
    evaluate_graph_result,
    run_graph_with_evaluation,
    batch_evaluate_samples
)
from simba.core.langfuse_config import get_langfuse_client


def format_scores(scores):
    """Format evaluation scores for display."""
    if not scores:
        return "No evaluation scores available."
    
    result = []
    for metric, score in scores.items():
        metric_name = metric.replace("_", " ").title()
        result.append(f"  {metric_name}: {score:.4f}")
    
    return "\n".join(result)


def run_direct_evaluation_example():
    """Run the graph and then evaluate the results."""
    print("\n=== Running Direct Evaluation Example ===")
    
    user_question = "What is Retrieval Augmented Generation?"
    print(f"Question: {user_question}")
    print("Running LangGraph RAG chain...")
    
    try:
        # Generate a thread ID for the checkpointer
        thread_id = str(uuid.uuid4())
        
        # Run the graph with proper configuration
        graph_input = {"messages": [{"role": "user", "content": user_question}]}
        result = graph.invoke(
            graph_input,
            config={"configurable": {"thread_id": thread_id}}
        )
        
        answer = result["messages"][-1].content
        print(f"\nAnswer: {answer}")
        
        # Get Langfuse client and create a trace
        langfuse = get_langfuse_client()
        trace = None
        if langfuse:
            trace = langfuse.trace(name="Post-execution evaluation")
            trace_id = trace.id
            print(f"Created Langfuse trace: {trace_id}")
        else:
            trace_id = None
            print("Langfuse client not available - evaluation will run without logging")
        
        # Evaluate the result
        print("\nRunning RAGAS evaluation...")
        scores = evaluate_graph_result(result, trace_id)
        
        # Complete the trace if we have one
        if trace:
            try:
                trace.update(status="success")
            except:
                pass
        
        print("\nEvaluation Scores:")
        print(format_scores(scores))
    
    except Exception as e:
        print(f"Error in direct evaluation example: {str(e)}")


def run_integrated_evaluation_example():
    """Run the graph with integrated evaluation."""
    print("\n=== Running Integrated Evaluation Example ===")
    
    user_question = "How does RAG improve language model responses?"
    print(f"Question: {user_question}")
    print("Running LangGraph RAG chain with integrated evaluation...")
    
    try:
        # Run the graph with evaluation
        result = run_graph_with_evaluation(
            user_question=user_question,
            trace_name="Integrated RAG evaluation"
        )
        
        print(f"\nAnswer: {result['answer']}")
        
        if result.get('trace_id'):
            print(f"Trace ID: {result['trace_id']}")
            print("You can view detailed spans and scores in the Langfuse UI.")
        
        print("\nEvaluation Scores:")
        print(format_scores(result.get('scores', {})))
    
    except Exception as e:
        print(f"Error in integrated evaluation example: {str(e)}")


def run_batch_example():
    """Run batch evaluation on predefined examples."""
    print("\n=== Running Batch Evaluation Example ===")
    
    # Sample questions to evaluate
    questions = [
        "What is Simba?",
        "How does vector search work?",
        "What are the benefits of RAG?"
    ]
    
    print("Processing multiple questions for batch evaluation...")
    
    try:
        # Run each question through the graph and collect results
        samples = []
        
        for i, question in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] Processing: {question}")
            
            try:
                # Generate a thread ID for the checkpointer
                thread_id = str(uuid.uuid4())
                
                # Run the graph with proper configuration
                graph_input = {"messages": [{"role": "user", "content": question}]}
                result = graph.invoke(
                    graph_input,
                    config={"configurable": {"thread_id": thread_id}}
                )
                
                # Extract data
                answer = result["messages"][-1].content
                documents = result.get("documents", [])
                
                # Convert documents to text if they're Document objects
                if documents and hasattr(documents[0], 'page_content'):
                    contexts = [doc.page_content for doc in documents]
                else:
                    contexts = documents
                
                # Add to samples
                samples.append({
                    "question": question,
                    "contexts": contexts,
                    "answer": answer
                })
            except Exception as e:
                print(f"  Error processing question '{question}': {str(e)}")
                # Add a placeholder with empty context if processing fails
                samples.append({
                    "question": question,
                    "contexts": ["Error retrieving context"],
                    "answer": "Error generating answer"
                })
            
            # Sleep to avoid rate limiting on API calls
            time.sleep(1)
        
        # Run batch evaluation if we have samples
        if samples:
            print("\nRunning batch RAGAS evaluation...")
            evaluation_results = batch_evaluate_samples(samples)
            
            if evaluation_results:
                print("\nBatch Evaluation Results:")
                for metric, score in evaluation_results.items():
                    print(f"  {metric}: {score}")
                
                # Save results to a file
                with open("ragas_batch_results.json", "w") as f:
                    json.dump(evaluation_results, f, indent=2)
                
                print("\nResults saved to ragas_batch_results.json")
            else:
                print("\nNo evaluation results were returned.")
        else:
            print("\nNo samples were collected for evaluation.")
    
    except Exception as e:
        print(f"Error in batch evaluation example: {str(e)}")


def run_interactive_example():
    """Run an interactive example where the user can input questions."""
    print("\n=== Running Interactive Example ===")
    print("Type your questions and see the RAG results with RAGAS evaluation metrics.")
    print("Type 'quit', 'exit', or 'q' to return to the main menu.")
    
    while True:
        # Get user input
        user_question = input("\nEnter your question: ")
        
        if user_question.lower() in ('quit', 'exit', 'q'):
            break
        
        if not user_question.strip():
            print("Please enter a valid question.")
            continue
        
        # Process the query with evaluation
        print("Running RAG pipeline with evaluation...")
        
        try:
            result = run_graph_with_evaluation(
                user_question=user_question
            )
            
            print(f"\nAnswer: {result['answer']}")
            
            if result.get('trace_id'):
                print(f"Trace ID: {result['trace_id']}")
            
            if result.get('scores'):
                print("\nEvaluation Scores:")
                print(format_scores(result['scores']))
                print("\nCheck the Langfuse UI to see the complete trace with all details.")
            else:
                print("\nNo evaluation scores available. Check logs for errors.")
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")


if __name__ == "__main__":
    print("=" * 80)
    print("RAGAS Evaluation for LangGraph RAG Chain".center(80))
    print("=" * 80)
    print("\nThis script demonstrates how to evaluate your RAG chain using RAGAS metrics")
    print("and log detailed traces to Langfuse for monitoring and debugging.")
    print("\nNote: Make sure Langfuse is running and properly configured in your .env file.")
    
    try:
        # Check if Langfuse client is available
        langfuse = get_langfuse_client()
        if langfuse:
            print("\n✅ Langfuse client initialized successfully.")
        else:
            print("\n⚠️  Langfuse client not available. Evaluation will run without logging.")
        
        # Run examples
        run_direct_evaluation_example()
        
        # Ask if the user wants to continue after the first example
        continue_running = input("\nContinue to the next example? (y/n): ")
        if continue_running.lower() not in ('y', 'yes'):
            print("\nExiting script. Thanks for using the RAGAS evaluator!")
            exit(0)
        
        run_integrated_evaluation_example()
        
        # Ask if the user wants to run more examples
        run_more = input("\nRun the batch evaluation example? (y/n): ")
        if run_more.lower() in ('y', 'yes'):
            run_batch_example()
        
        run_interactive = input("\nRun the interactive example? (y/n): ")
        if run_interactive.lower() in ('y', 'yes'):
            run_interactive_example()
        
        print("\nScript completed successfully. Thanks for using the RAGAS evaluator!")
    
    except Exception as e:
        print(f"\n❌ Error running script: {str(e)}")
        print("Please check your configuration and try again.") 