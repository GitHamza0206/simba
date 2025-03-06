# Simba Chatbot with Langfuse Integration

This directory contains the implementation of a LangGraph-based chatbot for Simba, integrated with Langfuse for tracing and evaluation.

## Setup

1. Install the required dependencies:

```bash
pip install langfuse
```

2. Set up a local Langfuse server (or use the Langfuse cloud service):

```bash
# Pull and start the Langfuse container
docker pull langfuse/langfuse:latest
docker run -d --name langfuse -p 3000:3000 langfuse/langfuse:latest
```

3. Access the Langfuse UI at http://localhost:3000

## How It Works

The Langfuse integration is implemented at the graph level, which means:

- All nodes (retrieve, grade, generate) are automatically traced
- All LLM calls, retrievals, and other operations are logged to Langfuse
- No need to add callback handlers to individual node functions

The integration is done by adding the Langfuse callback handler during graph compilation:

```python
# In graph.py
langfuse_handler = get_langfuse_callback_handler()
graph = workflow.compile(checkpointer=memory).with_config({"callbacks": [langfuse_handler]})
```

## Usage

Simply invoke the graph normally - Langfuse tracing happens automatically:

```python
from simba.chatbot.demo.graph import graph

# The graph already has Langfuse configured
result = graph.invoke({"messages": "your question here"})
```

## Configuration

The Langfuse configuration is defined in `langfuse_integration.py`. You can update the API keys and host if needed. 