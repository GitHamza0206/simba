import logging
from typing import List, Optional, Tuple, Dict, Any, Union
from psycopg2.extras import RealDictCursor, Json
import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer, text, bindparam, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from langchain.docstore.document import Document
from langchain.schema.embeddings import Embeddings
from simba.core.config import settings
from simba.models.simbadoc import SimbaDoc, MetadataType
from simba.database.postgres import PostgresDB, Base, DateTimeEncoder, SQLDocument
from simba.vector_store.base import VectorStoreBase
from simba.core.factories.embeddings_factory import get_embeddings
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import VectorStore
from uuid import uuid4
from langchain_community.retrievers import BM25Retriever
from simba.auth.auth_service import get_supabase_client
import numpy as np

supabase = get_supabase_client()

logger = logging.getLogger(__name__)

class ChunkEmbedding(Base):
    """SQLAlchemy model for chunks_embeddings table"""
    __tablename__ = 'chunks_embeddings'
    
    # Since LangChain Document uses string UUID, we'll use String type
    id = Column(String, primary_key=True, index=True)
    document_id = Column(String, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String, nullable=False)
    data = Column(JSONB, nullable=False, default={})
    embedding = Column(Vector(1536))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Define indexes using proper SQLAlchemy syntax
    __table_args__ = (
        # Index for faster user_id filtering
        {'schema': None}  # We'll create indexes separately in the ensure_text_search_index method
    )
    
    # Relationship to parent document
    document = relationship("SQLDocument", back_populates="chunks")
    
    @classmethod
    def from_langchain_doc(cls, doc: Document, document_id: str, user_id: str, embedding: List[float]) -> "ChunkEmbedding":
        """Create ChunkEmbedding from LangChain Document"""
        # Convert Document to dict format
        doc_dict = {
            "page_content": doc.page_content,
            "metadata": doc.metadata
        }
        
        return cls(
            id=doc.id,  # Use the LangChain document's ID directly as string
            document_id=document_id,
            user_id=user_id,
            data=json.loads(json.dumps(doc_dict, cls=DateTimeEncoder)),
            embedding=embedding
        )
    
    def to_langchain_doc(self) -> Document:
        """Convert to LangChain Document"""
        return Document(
            page_content=self.data["page_content"],
            metadata=self.data["metadata"]
        )

class PGVectorStore(VectorStore):
    """
    Custom PostgreSQL pgvector implementation using SQLAlchemy ORM.
    """
    
    def __init__(self, embedding_dim: int = 3072, create_indexes: bool = True):
        """
        Initialize the vector store.
        
        Args:
            embedding_dim: Dimension of the embedding vectors
            create_indexes: Whether to automatically create optimized indexes
        """
        self.embedding_dim = embedding_dim
        
        # Initialize PostgresDB if not already initialized
        self.db = PostgresDB()
        self._Session = self.db._Session
        
        # Initialize BM25 retriever as None, will be created on first use
        self._bm25_retriever = None
        self._bm25_docs = None
        
        # Log initialization
        logger.info("Vector store initialized")
    
    @property
    def embeddings(self) -> Optional[Embeddings]:
        """Access the query embedding object if available."""
        logger.debug(
            f"The embeddings property has not been "
            f"implemented for {self.__class__.__name__}"
        )
        return get_embeddings()
        
    def add_documents(self, documents: List[Document], document_id: str) -> bool:
        """Add documents to the store using SQLAlchemy ORM."""
        session = None
        try:
            session = self._Session()
            
            # Check if document exists
            existing_doc = session.query(SQLDocument).filter(SQLDocument.id == document_id).first()
            if not existing_doc:
                raise ValueError(f"Parent document {document_id} not found")
            
            # Get user_id from the document
            user_id = str(existing_doc.user_id)
            
            # Generate embeddings for all documents
            texts = [doc.page_content for doc in documents]
            embeddings = self.embeddings.embed_documents(texts)
            
            # Create ChunkEmbedding objects and explicitly set their IDs
            chunk_objects = []
            for doc, embedding in zip(documents, embeddings):
                chunk = ChunkEmbedding(
                    id=doc.id,  # Use the LangChain document's ID directly
                    document_id=document_id,
                    user_id=user_id,
                    data={
                        "page_content": doc.page_content,
                        "metadata": doc.metadata
                    },
                    embedding=embedding
                )
                chunk_objects.append(chunk)
            
            # Add all chunks to session
            session.add_all(chunk_objects)
            session.commit()
            
            logger.info(f"Successfully added {len(documents)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to add documents: {e}")
            raise  # Re-raise the exception to handle it at a higher level
        finally:
            if session:
                session.close()
    
    def count_chunks(self) -> int:
        """
        Count the total number of chunks in the store.
        
        Returns:
            The total number of chunks
        """
        session = None
        try:
            session = self._Session()
            return session.query(ChunkEmbedding).count()
        finally:
            if session:
                session.close()
    
    def get_document(self, document_id: str) -> Optional[SimbaDoc]:
        """
        Retrieve a document from the store.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            The retrieved document, or None if not found
        """
        session = None
        try:
            session = self._Session()
            doc = session.query(SQLDocument).filter(SQLDocument.id == document_id).first()
            return doc.to_simbadoc() if doc else None
        finally:
            if session:
                session.close()
    
    def _rerank_with_cross_encoder(self, query: str, initial_results: List[ChunkEmbedding], 
                                top_k: int = 10, model_name: str = 'cross-encoder/mmarco-mMiniLMv2-L12-H384-v1') -> List[ChunkEmbedding]:
        """
        Rerank initial results using a cross-encoder model.
        
        Args:
            query: The search query
            initial_results: Initial retrieval results to rerank
            top_k: Number of top results to return after reranking
            model_name: Name of the cross-encoder model to use
            
        Returns:
            Reranked list of ChunkEmbedding objects
        """
        try:
            from sentence_transformers import CrossEncoder
            
            # Initialize cross-encoder model
            cross_encoder = CrossEncoder(model_name)
            
            # Extract text content from results
            pairs = []
            for result in initial_results:
                # Extract page_content from the data JSONB field
                page_content = result.data.get('page_content', '')
                pairs.append((query, page_content))
            
            # Get cross-encoder scores
            scores = cross_encoder.predict(pairs)
            
            # Sort results by scores (highest first)
            reranked_results = [x for _, x in sorted(zip(scores, initial_results), reverse=True)]
            
            # Return top k results
            return reranked_results[:top_k]
            
        except ImportError:
            logger.warning("Could not import sentence_transformers. Reranking skipped. Install with 'pip install sentence-transformers'")
            return initial_results[:top_k]
        except Exception as e:
            logger.warning(f"Error during cross-encoder reranking: {e}. Using original ranking.")
            return initial_results[:top_k]

    def _get_bm25_retriever(self, user_id: str, k: int = 10) -> BM25Retriever:
        """
        Get or create BM25 retriever for a user.
        Caches the retriever and documents to avoid rebuilding for each query.
        """
        if self._bm25_retriever is None or self._bm25_docs is None:
            # Get all documents for this user
            self._bm25_docs = self.get_all_documents(user_id=user_id)
            logger.debug(f"Initialized BM25 with {len(self._bm25_docs)} documents")
            
            # Initialize BM25 retriever
            self._bm25_retriever = BM25Retriever.from_documents(
                self._bm25_docs,
                k=k,
                bm25_params={
                    "k1": 1.2,
                    "b": 0.75,
                }
            )
        
        return self._bm25_retriever

    def similarity_search(self, query: str, user_id: str, top_k: int = 10, 
                        hybrid_search: bool = True, alpha: float = 0.5,
                        rerank: bool = False, rerank_model: str = 'cross-encoder/ms-marco-MiniLM-L-12-v2',
                        rerank_factor: int = 4, 
                        use_bm25_first_pass: bool = True,
                        language: str = 'french') -> List[Document]:
        """
        Search for documents similar to a query, filtered by user_id.
        
        Args:
            query: The search query
            user_id: The user ID to filter results by
            top_k: The number of top results to return
            hybrid_search: Whether to use hybrid search (both vector and text search)
            alpha: Weight factor for blending vector and text scores (0.0-1.0)
            rerank: Whether to apply cross-encoder reranking to improve result order
            rerank_model: Name of the cross-encoder model to use for reranking
            rerank_factor: Number of initial candidates to retrieve for reranking
            use_bm25_first_pass: Whether to use BM25 for first-pass document retrieval
            language: The language to use for text search (default: 'french')
            
        Returns:
            A list of documents similar to the query
        """
        session = None
        try:
            # Get a session and its engine
            session = self._Session()
            conn = session.connection()
            cur = conn.connection.cursor(cursor_factory=RealDictCursor)
            
            if use_bm25_first_pass:
                first_pass_k = top_k * 3
                # Get BM25 retriever (will be cached after first use)
                bm25_retriever = self._get_bm25_retriever(user_id, first_pass_k)
                
                # Get top documents using BM25
                first_pass_docs = bm25_retriever.get_relevant_documents(query)
                logger.debug(f"BM25 returned {len(first_pass_docs)} documents")
                
                # Extract document IDs from first pass results
                first_pass_doc_ids = list({doc.metadata['document_id'] for doc in first_pass_docs})
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            query_embedding_array = np.array(query_embedding)
            # Convert numpy array to list for psycopg2
            query_embedding_list = query_embedding_array.tolist()
            
            # For reranking, we retrieve more initial candidates
            initial_top_k = top_k * rerank_factor if rerank else top_k
            
            # Prepare the SQL query
            if hybrid_search:
                # Hybrid search: combine vector similarity with text similarity
                sql = """
                    SELECT * FROM chunks_embeddings 
                    WHERE user_id = %s 
                """
                
                params = [user_id]
                
                if use_bm25_first_pass and first_pass_doc_ids:
                    sql += " AND document_id = ANY(%s) "
                    params.append(first_pass_doc_ids)
                
                sql += f"""
                    ORDER BY ({alpha} * (1 - (embedding <=> %s::vector)/2) + 
                             (1 - {alpha}) * ts_rank(to_tsvector(%s, data->>'page_content'), 
                                                  plainto_tsquery(%s, %s))) DESC
                    LIMIT %s
                """
                params.extend([query_embedding_list, language, language, query, initial_top_k])
                
            else:
                # Vector search only
                sql = """
                    SELECT * FROM chunks_embeddings 
                    WHERE user_id = %s 
                """
                
                params = [user_id]
                
                if use_bm25_first_pass and first_pass_doc_ids:
                    sql += " AND document_id = ANY(%s) "
                    params.append(first_pass_doc_ids)
                
                sql += """
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                params.extend([query_embedding_list, initial_top_k])
            
            # Execute query
            cur.execute(sql, params)
            rows = cur.fetchall()
            
            # Convert rows to ChunkEmbedding objects
            results = []
            for row in rows:
                # Create a document with the data from the row
                doc = Document(
                    page_content=row['data'].get('page_content', ''),
                    metadata=row['data'].get('metadata', {})
                )
                results.append(doc)
            
            # Apply cross-encoder reranking if requested
            if rerank and results:
                # Convert rows to ChunkEmbedding objects for reranking
                chunk_objects = []
                for row in rows:
                    chunk = ChunkEmbedding(
                        id=row['id'],
                        document_id=row['document_id'],
                        user_id=row['user_id'],
                        data=row['data'],
                        embedding=row['embedding']
                    )
                    chunk_objects.append(chunk)
                
                # Rerank using cross-encoder
                reranked_chunks = self._rerank_with_cross_encoder(
                    query=query,
                    initial_results=chunk_objects,
                    top_k=top_k,
                    model_name=rerank_model
                )
                
                # Convert reranked chunks to documents
                results = [chunk.to_langchain_doc() for chunk in reranked_chunks]
            elif len(results) > top_k:
                # If we retrieved more results than needed (for reranking) but didn't rerank,
                # trim to the requested top_k
                results = results[:top_k]
            
            return results
        
        finally:
            if session:
                session.close()

    def from_texts(
        self,
        texts: List[str],
        embedding: Optional[Embeddings] = None,
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add texts to the vector store.
        
        Args:
            texts: List of texts to add
            embedding: Optional embedding function (will use self.embeddings if not provided)
            metadatas: Optional list of metadatas associated with the texts
            ids: Optional list of IDs to associate with the texts
            **kwargs: Additional arguments (must include document_id)
            
        Returns:
            List of IDs of the added texts
        """
        session = None
        try:
            session = self._Session()
            
            # Get document_id from kwargs
            document_id = kwargs.get('document_id')
            if not document_id:
                raise ValueError("document_id is required in kwargs")
            
            # Check if document exists
            existing_doc = session.query(SQLDocument).filter(SQLDocument.id == document_id).first()
            if not existing_doc:
                raise ValueError(f"Parent document {document_id} not found")
            
            # Get user_id from the document
            user_id = existing_doc.user_id

            # Use provided embeddings or default to self.embeddings
            embeddings_func = embedding or self.embeddings
            
            # Generate embeddings
            embeddings = embeddings_func.embed_documents(texts)
            
            # Handle metadata
            if not metadatas:
                metadatas = [{} for _ in texts]
            
            # Handle IDs
            if not ids:
                ids = [str(uuid.uuid4()) for _ in texts]
            
            # Create chunk objects
            chunk_objects = []
            for text, metadata, embedding_vector, chunk_id in zip(texts, metadatas, embeddings, ids):
                chunk = ChunkEmbedding(
                    id=chunk_id,
                    document_id=document_id,
                    user_id=user_id,
                    data={
                        "page_content": text,
                        "metadata": metadata
                    },
                    embedding=embedding_vector
                )
                chunk_objects.append(chunk)
            
            # Add all chunks to session
            session.add_all(chunk_objects)
            session.commit()
            
            logger.info(f"Successfully added {len(texts)} texts for document {document_id}")
            return ids
            
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Failed to add texts: {e}")
            raise
        finally:
            if session:
                session.close()

    def get_documents(self, document_ids: List[str], user_id: str) -> List[Document]:
        """Get documents by their IDs, filtered by user_id."""
        session = None
        try:
            session = self._Session()
            chunks = session.query(ChunkEmbedding).filter(
                ChunkEmbedding.document_id.in_(document_ids),
                ChunkEmbedding.user_id == user_id
            ).all()
            return [chunk.to_langchain_doc() for chunk in chunks]
        finally:
            if session:
                session.close()

    def get_all_documents(self, user_id: str) -> List[Document]:
        """Get all documents from the store, optionally filtered by user_id."""
        session = None
        try:
            session = self._Session()
            query = session.query(ChunkEmbedding).filter(ChunkEmbedding.user_id == user_id)
                
            chunks = query.all()
            # Modify this to ensure document_id is in metadata
            return [
                Document(
                    page_content=chunk.data["page_content"],
                    metadata={
                        **chunk.data.get("metadata", {}),
                        "document_id": chunk.document_id  # Explicitly add document_id
                    }
                ) 
                for chunk in chunks
            ]
        finally:
            if session:
                session.close()

    def delete_documents(self, doc_id: str) -> bool:
        """Delete documents from the store using SQLAlchemy ORM, optionally filtered by user_id."""
        session = None
        try:
            session = self._Session()
            
            user_id = supabase.auth.get_user().user.id
            #verify that user_id has access to the document
            doc = session.query(SQLDocument).filter(SQLDocument.id == doc_id, SQLDocument.user_id == user_id).first()
            if not doc:
                raise ValueError(f"User {user_id} does not have access to document {doc_id}")

            # Build the base query using SQLAlchemy
            query = session.query(ChunkEmbedding).filter(ChunkEmbedding.document_id == doc_id)
            
            # Execute delete
            deleted_count = query.delete(synchronize_session=False)
            session.commit()
            
            logger.info(f"Successfully deleted {deleted_count} chunks")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def clear_store(self, user_id: str = None) -> bool:
        """Clear all documents from the store, optionally filtered by user_id."""
        session = None
        try:
            session = self._Session()
            
            # Build query based on whether user_id is provided
            query = session.query(ChunkEmbedding)
            if user_id:
                query = query.filter(ChunkEmbedding.user_id == user_id)
                
            query.delete(synchronize_session=False)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to clear store: {e}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def update_document(self, document_id: str, new_document: Document, user_id: str = None) -> bool:
        """Update a document in the store."""
        session = None
        try:
            session = self._Session()
            # Generate new embedding
            embedding = self.embeddings.embed_documents([new_document.page_content])[0]
            
            # Build query to find the existing chunk
            query = session.query(ChunkEmbedding).filter(
                ChunkEmbedding.document_id == document_id
            )
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(ChunkEmbedding.user_id == user_id)
                
            chunk = query.first()
            
            if not chunk:
                return False
            
            # Get user_id from the existing document record (no need to change user_id)
            # user_id remains the same as in the original chunk
                
            # Update the chunk with new data
            doc_dict = {
                "page_content": new_document.page_content,
                "metadata": new_document.metadata
            }
            chunk.data = json.loads(json.dumps(doc_dict, cls=DateTimeEncoder))
            chunk.embedding = embedding
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def check_cross_encoder_dependencies(self) -> bool:
        """
        Check if necessary dependencies for cross-encoder reranking are installed.
        Returns True if dependencies are available, False otherwise.
        """
        try:
            import sentence_transformers
            from sentence_transformers import CrossEncoder
            logger.info("Cross-encoder dependencies are available.")
            return True
        except ImportError:
            logger.warning(
                "Cross-encoder dependencies not found. "
                "Install with: pip install sentence-transformers"
            )
            return False

if __name__ == "__main__":
    # Initialize vector store with optimized indexes
    pgvector = PGVectorStore(create_indexes=True)
    health = pgvector.health_check()
    print(f"Vector store health: {health}")
    
    # Create test documents
    from langchain.schema import Document as LangchainDocument
    from simba.models.simbadoc import SimbaDoc, MetadataType
    
    # Test user ID
    test_user_id = "test_user_123"
    
    # Create multiple test documents
    doc1 = SimbaDoc(
        id="test_doc_1",
        documents=[
            LangchainDocument(page_content="This is a test document for pgvector", metadata={"source": "test", "document_id": "test_doc_1"})
        ],
        metadata=MetadataType(filename="test1.txt", type="text", enabled=True)
    )
    
    doc2 = SimbaDoc(
        id="test_doc_2",
        documents=[
            LangchainDocument(page_content="Another test document with different content", metadata={"source": "test", "document_id": "test_doc_2"})
        ],
        metadata=MetadataType(filename="test2.txt", type="text", enabled=True)
    )
    
    # Insert into database first to associate with user
    db = PostgresDB()
    db.insert_document(doc1, test_user_id)
    db.insert_document(doc2, test_user_id)
    
    # Test adding multiple documents
    print(f"Adding multiple documents to vector store...")
    # Add documents to vector store
    pgvector.add_documents(doc1.documents, doc1.id)
    pgvector.add_documents(doc2.documents, doc2.id)
    
    # Count chunks
    chunk_count = pgvector.count_chunks()
    print(f"Total chunks in store: {chunk_count}")
    
    # Test retrieving each document
    retrieved_doc1 = pgvector.get_document(doc1.id)
    retrieved_doc2 = pgvector.get_document(doc2.id)
    
    print(f"Retrieved document: {retrieved_doc1.id}, with {len(retrieved_doc1.documents)} chunks")
    print(f"Document content: {retrieved_doc1.documents[0].page_content}")
    
    print(f"Retrieved document: {retrieved_doc2.id}, with {len(retrieved_doc2.documents)} chunks")
    print(f"Document content: {retrieved_doc2.documents[0].page_content}")
    
    # Search for similar documents using vector search only
    print(f"\nSearching for 'test document' using vector search...")
    results = pgvector.similarity_search("test document", test_user_id, hybrid_search=False, rerank=False)
    print(f"Found {len(results)} results")
    for doc in results:
        print(f"- {doc.page_content} (score: {doc.metadata.get('score', 'N/A')})")
    
    # Search using hybrid search (vector + full-text)
    print(f"\nSearching for 'another document' using hybrid search without reranking...")
    results = pgvector.similarity_search("another document", test_user_id, hybrid_search=True, rerank=False)
    print(f"Found {len(results)} results")
    for doc in results:
        print(f"- {doc.page_content} (score: {doc.metadata.get('score', 'N/A')})")
    
    # Check if cross-encoder dependencies are available
    has_cross_encoder = pgvector.check_cross_encoder_dependencies()
    
    if has_cross_encoder:
        # Search using hybrid search with reranking (optimized retrieval pipeline)
        print(f"\nSearching for 'document test' using the full optimized retrieval pipeline...")
        print(f"(Hybrid search → 20 candidates → Cross-encoder reranking → Top 5 results)")
        results = pgvector.similarity_search(
            "document test", 
            test_user_id, 
            top_k=5,               # Return 5 final results
            hybrid_search=True,    # Use hybrid search
            rerank=True,           # Apply cross-encoder reranking
            rerank_factor=4,       # Get 4x more initial candidates (20 for reranking)
            use_bm25_first_pass=True,
            first_pass_k=5
        )
        print(f"Found {len(results)} results after optimized retrieval pipeline")
        for doc in results:
            print(f"- {doc.page_content} (score: {doc.metadata.get('score', 'N/A')})")
    else:
        print("\nCross-encoder reranking not available. Install dependencies to enable this feature.")
    
    # Test with BM25 first-pass retrieval only (no hybrid search or reranking)
    print(f"\nSearching for 'document test' using BM25 first-pass and then vector search...")
    results = pgvector.similarity_search(
        "document test", 
        test_user_id, 
        top_k=5,               
        hybrid_search=False,   # Use vector search only for second pass
        rerank=False,          # No reranking
        use_bm25_first_pass=True,  # Enable BM25 first-pass
        first_pass_k=5         # Get top 5 documents from BM25
    )
    print(f"Found {len(results)} results using BM25 + vector search pipeline")
    for doc in results:
        print(f"- {doc.page_content} (score: {doc.metadata.get('score', 'N/A')})")
    
    print("\nTest completed successfully!")
    
