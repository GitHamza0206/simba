# RAG Evaluation with RAGAS and Langfuse

This module provides utilities for evaluating RAG (Retrieval Augmented Generation) pipelines using RAGAS metrics and logging results to Langfuse for monitoring and debugging.

## Features

- Evaluate RAG results using RAGAS metrics:
  - **Faithfulness**: Measures factual consistency of answers with retrieved contexts
  - **Answer Relevancy**: Measures how relevant the answer is to the user's question
  - **Context Recall**: Measures how well the retrieved context covers information needed for the answer
  - **Context Precision**: Measures how focused and relevant the retrieved context is

- Integration with Langfuse:
  - Create traces for each query
  - Log spans for each step of the RAG pipeline
  - Record evaluation scores for each query
  - Enable detailed debugging and performance monitoring

## How to Use

### Evaluating a Single Query

```python
from simba.chatbot.demo.graph import graph
from simba.chatbot.evaluation.rag_evaluation import run_graph_with_evaluation

# Run the graph with integrated evaluation
result = run_graph_with_evaluation(
    user_question="What is Retrieval Augmented Generation?",
    trace_name="RAG query"
)

# Access the results
answer = result["answer"]
trace_id = result["trace_id"]
scores = result["scores"]

# Print evaluation scores
for metric, score in scores.items():
    print(f"{metric}: {score:.4f}")
```

### Evaluating an Existing Graph Result

```python
from simba.chatbot.demo.graph import graph
from simba.chatbot.evaluation.rag_evaluation import evaluate_graph_result
from simba.core.langfuse_config import get_langfuse_client

# Run the graph
graph_input = {"messages": [{"role": "user", "content": "What is RAG?"}]}
result = graph.invoke(graph_input)

# Create a Langfuse trace
langfuse = get_langfuse_client()
trace = langfuse.trace(name="Post-execution evaluation")

# Evaluate the result
scores = evaluate_graph_result(result, trace_id=trace.id)

# End the trace
trace.end()
```

### Batch Evaluation

```python
from simba.chatbot.evaluation.rag_evaluation import batch_evaluate_samples

# Prepare sample data
samples = [
    {
        "question": "What is Simba?",
        "contexts": ["Simba is a knowledge management system..."],
        "answer": "Simba is a knowledge management system that..."
    },
    # More samples...
]

# Run batch evaluation
evaluation_results = batch_evaluate_samples(samples)
```

## Example Scripts

Check out the example scripts in the `examples/` directory:

- `rag_evaluation_example.py`: Demonstrates different ways to evaluate your RAG pipeline

## Configuration

The module uses Langfuse for tracing, which requires the following environment variables:

```
LANGFUSE_PUBLIC_KEY="your-public-key"
LANGFUSE_SECRET_KEY="your-secret-key"
LANGFUSE_HOST="http://localhost:3000" # or your Langfuse host
```

The RAGAS evaluation requires OpenAI API access for the evaluator LLM and embeddings:

```
OPENAI_API_KEY="your-openai-api-key"
```

## Metrics Interpretation

- **Faithfulness**: Scores near 1.0 indicate the answer is factually consistent with the retrieved context
- **Answer Relevancy**: Scores near 1.0 indicate the answer directly addresses the user's question
- **Context Recall**: Scores near 1.0 indicate the retrieved context contains most information needed to answer
- **Context Precision**: Scores near 1.0 indicate the retrieved context is focused and relevant 