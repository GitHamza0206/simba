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
from langchain_core.documents import Document
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
from collections import defaultdict

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

    def _retrieve_with_bm25(self, query: str, user_id: str, k: int = 30) -> List[str]:
        """
        Perform first-pass BM25 retrieval to get candidate document IDs.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            k: Number of documents to retrieve
            
        Returns:
            List of document IDs from BM25 retrieval
        """
        # Get BM25 retriever (will be cached after first use)
        bm25_retriever = self._get_bm25_retriever(user_id, k)
        
        # Get top documents using BM25
        first_pass_docs = bm25_retriever.get_relevant_documents(query)
        logger.debug(f"BM25 returned {len(first_pass_docs)} documents")
        
        # Extract document IDs from first pass results
        first_pass_doc_ids = list({doc.metadata['document_id'] for doc in first_pass_docs})
        
        return first_pass_doc_ids

    def _retrieve_with_dense_vector(self, query: str, user_id: str, top_k: int, 
                               document_ids: Optional[List[str]] = None) -> List[Document]:
        """
        Perform pure vector similarity search.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            top_k: Number of results to retrieve
            document_ids: Optional list of document IDs to filter by (from BM25)
            
        Returns:
            List of Document objects with results
        """
        session = None
        try:
            # Get a session and its engine
            session = self._Session()
            conn = session.connection()
            cur = conn.connection.cursor(cursor_factory=RealDictCursor)
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            query_embedding_array = np.array(query_embedding)
            # Convert numpy array to list for psycopg2
            query_embedding_list = query_embedding_array.tolist()
            
            # Prepare the SQL query
            sql = """
                SELECT * FROM chunks_embeddings 
                WHERE user_id = %s 
            """
            
            params = [user_id]
            
            if document_ids:
                sql += " AND document_id = ANY(%s) "
                params.append(document_ids)
            
            sql += """
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            params.extend([query_embedding_list, top_k])
            
            # Execute query
            cur.execute(sql, params)
            rows = cur.fetchall()
            
            # Convert rows to Document objects
            results = []
            for row in rows:
                # Create a document with the data from the row
                doc = Document(
                    page_content=row['data'].get('page_content', ''),
                    metadata={
                        **row['data'].get('metadata', {}),
                        'id': row['id'],
                        'document_id': row['document_id']
                    }
                )
                results.append(doc)
            
            return results
        
        finally:
            if session:
                session.close()

    def _retrieve_with_text_search(self, query: str, user_id: str, top_k: int, 
                                 document_ids: Optional[List[str]] = None,
                                 language: str = 'french') -> List[Document]:
        """
        Perform text-based search using PostgreSQL's full-text search.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            top_k: Number of results to retrieve
            document_ids: Optional list of document IDs to filter by
            language: Language for text search
            
        Returns:
            List of Document objects with results
        """
        session = None
        try:
            # Get a session and its engine
            session = self._Session()
            conn = session.connection()
            cur = conn.connection.cursor(cursor_factory=RealDictCursor)
            
            # Prepare the SQL query for text search
            sql = """
                SELECT * FROM chunks_embeddings 
                WHERE user_id = %s 
            """
            
            params = [user_id]
            
            if document_ids:
                sql += " AND document_id = ANY(%s) "
                params.append(document_ids)
            
            sql += f"""
                ORDER BY ts_rank(to_tsvector(%s, data->>'page_content'), 
                               plainto_tsquery(%s, %s)) DESC
                LIMIT %s
            """
            params.extend([language, language, query, top_k])
            
            # Execute query
            cur.execute(sql, params)
            rows = cur.fetchall()
            
            # Convert rows to Document objects
            results = []
            for row in rows:
                # Create a document with the data from the row
                doc = Document(
                    page_content=row['data'].get('page_content', ''),
                    metadata={
                        **row['data'].get('metadata', {}),
                        'id': row['id'],
                        'document_id': row['document_id']
                    }
                )
                results.append(doc)
            
            return results
        
        finally:
            if session:
                session.close()

    def _fuse_results_rrf(self, *ranked_lists: List[Document], k: int = 60, top_k: int = 100) -> List[Document]:
        """
        Fuse multiple result lists using Reciprocal Rank Fusion.
        
        Args:
            ranked_lists: Multiple lists of Documents in rank order
            k: RRF constant (default=60)
            top_k: Number of results to return after fusion
            
        Returns:
            List of fused Document objects
        """
        # Create a mapping from document ID to document object
        doc_map = {}
        
        # Calculate RRF scores
        scores = defaultdict(float)
        for lst in ranked_lists:
            for rank, doc in enumerate(lst, start=1):
                doc_id = doc.metadata.get('id')
                if doc_id is None:
                    continue
                
                # Store document for later retrieval
                doc_map[doc_id] = doc
                
                # Add RRF score
                scores[doc_id] += 1 / (k + rank)
        
        # Sort by score and get top_k document IDs
        top_ids = [d for d, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)][:top_k]
        
        # Return documents in the new fused order
        return [doc_map[doc_id] for doc_id in top_ids if doc_id in doc_map]

    def similarity_search(self, query: str, user_id: str, top_k: int = 200,
                        bm25_k: int = 100, dense_k: int = 100,
                        use_bm25_first_pass: bool = True,
                        language: str = 'french') -> List[Document]:
        """
        Search for documents similar to a query, filtered by user_id.
        Uses a fusion of BM25 and dense retrieval results.
        
        Args:
            query: The search query
            user_id: The user ID to filter results by
            top_k: The number of top results to return after fusion (default: 200)
            bm25_k: Number of results to retrieve from BM25 (default: 100)
            dense_k: Number of results to retrieve from dense vectors (default: 100)
            use_bm25_first_pass: Whether to use BM25 retrieval
            language: The language to use for text search (default: 'french')
            
        Returns:
            A list of documents similar to the query
        """
        # Step 1: Sparse BM25 retrieval
        sparse_results = []
        if use_bm25_first_pass:
            # Get document IDs from BM25
            bm25_doc_ids = self._retrieve_with_bm25(query, user_id, bm25_k)
            # Get actual documents from database with text search ranking
            sparse_results = self._retrieve_with_text_search(
                query=query,
                user_id=user_id,
                top_k=bm25_k,
                document_ids=bm25_doc_ids,
                language=language
            )
        
        # Step 2: Dense vector retrieval
        dense_results = self._retrieve_with_dense_vector(
            query=query,
            user_id=user_id,
            top_k=dense_k,
            document_ids=None  # Don't filter by BM25 results for pure dense retrieval
        )
        
        # Step 3: Fuse results using RRF
        if use_bm25_first_pass and sparse_results:
            fused_results = self._fuse_results_rrf(
                sparse_results, 
                dense_results,
                k=60, 
                top_k=top_k
            )
        else:
            # If no BM25, just use dense results
            fused_results = dense_results[:top_k]
        
        # Return fused results
        return fused_results

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

    def rerank_results(self, query: str, initial_results: List[Document], top_k: int = 20, 
                      model_name: str = 'cross-encoder/ms-marco-MiniLM-L-12-v2') -> List[Document]:
        """
        Rerank retrieval results using cross-encoder.
        
        Args:
            query: Search query
            initial_results: Initial retrieval results as Documents
            top_k: Number of results to return (default: 20)
            model_name: Cross-encoder model to use
            
        Returns:
            Reranked list of Document objects
        """
        try:
            from sentence_transformers import CrossEncoder
            
            # Initialize cross-encoder model
            cross_encoder = CrossEncoder(model_name)
            
            # Extract text content from results
            pairs = []
            for doc in initial_results:
                pairs.append((query, doc.page_content))
            
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

    def context_compression(self, query: str, documents: List[Document], num_passages: int = 5) -> List[Document]:
        """
        Select the most relevant passages for context compression.
        
        Args:
            query: Search query
            documents: List of documents to compress
            num_passages: Number of passages to select (default: 5, range 4-6)
            
        Returns:
            Compressed list of Document objects
        """
        # Simple implementation - just take the top n documents
        # In a production system, this could be replaced with more sophisticated
        # context compression like xRAG/RECOMP
        
        # Ensure num_passages is in the 4-6 range
        num_passages = max(4, min(6, num_passages))
        
        # Take the top n passages
        return documents[:num_passages]

