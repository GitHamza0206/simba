from typing import Dict, List, Optional

import asyncio
from dotenv import load_dotenv
from simba.core.langfuse_config import get_langfuse_client
from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.metrics import (
    AnswerRelevancy,
    Faithfulness,
    ContextRecall,
    ContextPrecision,
)
from ragas.llms import LangchainLLMWrapper
from ragas.dataset_schema import SingleTurnSample
from simba.chatbot.demo.graph import graph

client = get_langfuse_client()


class RAGASEvaluator:
    """RAGAS evaluator for RAG pipelines with Langfuse integration."""
    
    def __init__(self, evaluator_model: str = "gpt-4", embedding_model: str = "text-embedding-ada-002"):
        """
        Initialize the RAGAS evaluator.
        
        Args:
            evaluator_model: The model to use for RAGAS evaluation
            embedding_model: The embedding model to use for similarity metrics
        """
        self.langfuse = get_langfuse_client()
        self.evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model=evaluator_model))
        
        # Initialize embeddings for metrics that require them
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # Create metrics with appropriate configuration
        self.metrics = [
            Faithfulness(llm=self.evaluator_llm),
            AnswerRelevancy(llm=self.evaluator_llm, embeddings=self.embeddings),
            ContextRecall(llm=self.evaluator_llm),
            ContextPrecision(llm=self.evaluator_llm)
        ]
    
    async def evaluate_sample(self, sample: SingleTurnSample, trace_id: Optional[str] = None) -> Dict[str, float]:
        """
        Evaluate a single RAG query using RAGAS metrics and log results to Langfuse.
        
        Args:
            sample: A RAGAS sample containing user_input, retrieved_contexts, and response
            trace_id: Optional Langfuse trace ID to log results to
            
        Returns:
            Dictionary of metric scores
        """
        scores = {}
        for metric in self.metrics:
            try:
                scores[metric.name] = await metric.single_turn_ascore(sample)
            except Exception as e:
                print(f"Error evaluating with metric '{metric.name}': {str(e)}")
                scores[metric.name] = 0.0
        
        # Log scores to Langfuse if trace_id is provided
        if trace_id and self.langfuse:
            try:
                trace = self.langfuse.get_trace(trace_id)
                for metric_name, score in scores.items():
                    # Check if score method exists, otherwise use the observation method
                    if hasattr(trace, 'score'):
                        trace.score(name=f"ragas:{metric_name}", value=score)
                    else:
                        trace.observation(
                            name=f"ragas:{metric_name}",
                            value=score,
                            level="info",
                            metadata={"metric": metric_name}
                        )
            except Exception as e:
                print(f"Error logging scores to Langfuse: {str(e)}")
        
        return scores
    
    def create_sample(
        self, 
        user_question: str, 
        retrieved_docs: List, 
        model_answer: str
    ) -> SingleTurnSample:
        """
        Create a RAGAS evaluation sample from query data.
        
        Args:
            user_question: The user's question
            retrieved_docs: List of retrieved documents/contexts
            model_answer: The model's generated answer
            
        Returns:
            A RAGAS SingleTurnSample for evaluation
        """
        # Convert retrieved docs to list of strings if they're Document objects
        if retrieved_docs and hasattr(retrieved_docs[0], 'page_content'):
            contexts = [doc.page_content for doc in retrieved_docs]
        else:
            contexts = retrieved_docs
            
        return SingleTurnSample(
            user_input=user_question,
            retrieved_contexts=contexts,
            response=model_answer
        )
    
    def batch_evaluate(self, samples: List[Dict]) -> Dict:
        """
        Run RAGAS evaluation on a batch of samples and return the aggregate results.
        
        Args:
            samples: List of dictionaries with keys 'question', 'contexts', 'answer'
            
        Returns:
            Dictionary of evaluation results
        """
        try:
            data = {
                "question": [s["question"] for s in samples],
                "contexts": [s["contexts"] for s in samples],
                "answer": [s["answer"] for s in samples]
            }
            
            eval_dataset = Dataset.from_dict(data)
            
            metric_names = [m.name for m in self.metrics]
            
            # Run RAGAS evaluation
            evaluation_results = evaluate(
                dataset=eval_dataset,
                metrics=metric_names,
                llm=self.evaluator_llm,
                embeddings=self.embeddings
            )
            
            return evaluation_results
        except Exception as e:
            print(f"Error in batch evaluation: {str(e)}")
            return {}


if __name__ == "__main__":
    # Example usage
    evaluator = RAGASEvaluator()
    
    # Create a sample evaluation
    sample = evaluator.create_sample(
        user_question="What is Simba?",
        retrieved_docs=["Simba is a portable knowledge management system designed for RAG applications."],
        model_answer="Simba is a portable knowledge management system that helps organize and retrieve information."
    )
    
    try:
        # Run evaluation asynchronously
        scores = asyncio.run(evaluator.evaluate_sample(sample))
        print("Evaluation Scores:")
        for metric, score in scores.items():
            print(f"  {metric}: {score:.4f}")
    except Exception as e:
        print(f"Error running evaluation: {str(e)}")