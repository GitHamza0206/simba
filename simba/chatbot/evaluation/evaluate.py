import asyncio
from ragas.dataset_schema import SingleTurnSample
from simba.chatbot.evaluation.evaluation_config import get_langfuse_client, get_ragas_metrics
from simba.chatbot.evaluation.prepare_dataset import load_from_csv
# Get the Langfuse client and Ragas metrics
langfuse = get_langfuse_client()
metrics = get_ragas_metrics()

async def score_with_ragas(query, retrieved_contexts, answer):
    """
    Score a single query-contexts-answer triplet using Ragas metrics.
    
    Args:
        query (str): The user's question
        retrieved_contexts (list): List of context strings used for answering
        answer (str): The generated answer
        
    Returns:
        dict: Dictionary of metric names to scores
    """
    scores = {}
    for metric in metrics:
        sample = SingleTurnSample(
            user_input=query,
            retrieved_contexts=retrieved_contexts,
            response=answer,
        )
        print(f"Calculating score for {metric.name}")
        scores[metric.name] = await metric.single_turn_ascore(sample)
    return scores

def evaluate_rag_response(question, contexts, answer, trace_name="rag"):
    """
    Evaluate a RAG response and log the results to Langfuse.
    
    Args:
        question (str): The user's question
        contexts (list): The context passages used for generation
        answer (str): The generated answer
        trace_name (str): Name for the Langfuse trace
        
    Returns:
        dict: The evaluation scores
    """
    # Create a new Langfuse trace and log pipeline steps
    trace = langfuse.trace(name=trace_name)
    trace.span(name="retrieval", input={'question': question}, output={'contexts': contexts})
    trace.span(name="generation", input={'question': question, 'contexts': contexts}, output={'answer': answer})
    
    # Run the evaluation
    ragas_scores = asyncio.run(score_with_ragas(question, contexts, answer))
    
    # Log scores to Langfuse
    for metric_name, score in ragas_scores.items():
        trace.score(name=metric_name, value=score)
    
    print("Evaluation complete. Check your Langfuse dashboard for scores!")
    return ragas_scores

# Example usage
if __name__ == "__main__":
    import os
    dataset_path = os.path.join(os.path.dirname(__file__), "sample_questions.csv")
    dataset = load_from_csv(dataset_path,question_col="question",contexts_col="contexts",answer_col="answer")
    for sample in dataset:
        question = sample.question
        contexts = sample.contexts
        answer = sample.answer
        scores = evaluate_rag_response(question, contexts, answer)
        print(scores)
        print("--------------------------------")
        if input("break ?") == "b":
            break
