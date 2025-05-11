from simba.vector_store.pgvector import PGVectorStore

# Initialize vector store for context compression
vector_store = PGVectorStore()

def compress(state):
    """
    Compress reranked documents to provide optimal context for the LLM

    Args:
        state (dict): The current graph state containing reranked documents

    Returns:
        state (dict): Updated state with compressed documents (4-6 passages)
    """
    try:
        print("---CONTEXT COMPRESSION---")
        question = state["question"]
        
        # Use reranked documents as input for compression
        documents = state["reranked_documents"]
        
        print(f"Compressing {len(documents)} documents")
        
        # Apply context compression to select optimal passages
        compressed_docs = vector_store.context_compression(
            query=question,
            documents=documents,
            num_passages=5  # Default to 5 passages (range 4-6)
        )
        
        print(f"Compressed to {len(compressed_docs)} passages")
        
        # Store compressed documents in their own field
        return {"compressed_documents": compressed_docs}
    except KeyError as e:
        print(f"Error compressing documents: {e}")
        # Return empty compressed documents if compression fails
        return {"compressed_documents": []} 