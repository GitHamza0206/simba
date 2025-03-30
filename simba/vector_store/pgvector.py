import logging
from typing import List, Optional, Tuple, Dict, Any, Union
from psycopg2.extras import RealDictCursor, Json
import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    
    def __init__(self, embedding_dim: int = 1536, create_indexes: bool = True):
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
        
        # Ensure schema and optimized indexes are properly set up
        if create_indexes:
            try:
                # Create text search indexes
                self.ensure_text_search_index()
                
                # Create vector similarity index
                # Adjust lists parameter based on expected dataset size
                self.create_vector_index(index_type='ivfflat', lists=100)
                
                logger.info("Vector store initialized with optimized indexes")
            except Exception as e:
                logger.warning(f"Failed to create optimized indexes on initialization: {e}")
                logger.warning("Search performance may not be optimal. Call ensure_text_search_index() and create_vector_index() explicitly.")
    
    @property
    def embeddings(self) -> Optional[Embeddings]:
        """Access the query embedding object if available."""
        logger.debug(
            f"The embeddings property has not been "
            f"implemented for {self.__class__.__name__}"
        )
        return get_embeddings()
        
        # Ensure schema exists
        # self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure the required database schema exists."""
        try:
            if not self.db._engine:
                raise ValueError("Database engine not initialized")
                
            # First ensure vector extension exists
            with self.db._engine.connect() as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
            
            # Create tables
            Base.metadata.create_all(self.db._engine)
            logger.info("Vector store schema initialized correctly")
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise

    def create_vector_index(self, index_type: str = 'ivfflat', lists: int = 100) -> bool:
        """
        Create an optimized index for vector similarity search.
        
        Args:
            index_type: Type of index ('ivfflat' or 'hnsw')
            lists: Number of lists for IVFFlat index (adjust based on dataset size)
                   For small datasets (< 10k): 10-50
                   For medium datasets (10k-1M): 100-500
                   For large datasets (> 1M): 500-1000
                   
        Returns:
            True if index was created successfully, False otherwise
        """
        try:
            if not self.db._engine:
                raise ValueError("Database engine not initialized")
                
            with self.db._engine.connect() as conn:
                # First ensure pgvector extension exists
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                
                # Drop existing index if it exists
                conn.execute(text(
                    "DROP INDEX IF EXISTS idx_chunks_embeddings_vector"
                ))
                
                # Create the specified index type
                if index_type.lower() == 'ivfflat':
                    # IVFFlat index with cosine distance
                    conn.execute(text(
                        f"CREATE INDEX idx_chunks_embeddings_vector ON chunks_embeddings "
                        f"USING ivfflat (embedding vector_cosine_ops) WITH (lists = {lists})"
                    ))
                    logger.info(f"Created IVFFlat index with {lists} lists")
                elif index_type.lower() == 'hnsw':
                    # HNSW index (available in pgvector 0.5.0+)
                    conn.execute(text(
                        "CREATE INDEX idx_chunks_embeddings_vector ON chunks_embeddings "
                        "USING hnsw (embedding vector_cosine_ops)"
                    ))
                    logger.info("Created HNSW index")
                else:
                    raise ValueError(f"Unsupported index type: {index_type}. Use 'ivfflat' or 'hnsw'")
                    
                conn.commit()
                
            return True
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return False

    def ensure_text_search_index(self):
        """Ensure the text search index exists for hybrid search."""
        try:
            if not self.db._engine:
                raise ValueError("Database engine not initialized")
                
            with self.db._engine.connect() as conn:
                # Create GIN index for full-text search on the extracted page_content
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_chunks_embeddings_page_content_gin "
                    "ON chunks_embeddings "
                    "USING GIN (to_tsvector('english', jsonb_extract_path_text(data, 'page_content')))"
                ))
                # Index for faster user_id filtering if not already exists
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_chunks_embeddings_user_id "
                    "ON chunks_embeddings (user_id)"
                ))
                conn.commit()
                
            logger.info("Text search indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create text search index: {e}")
            return False

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
                                top_k: int = 10, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2') -> List[ChunkEmbedding]:
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

    def similarity_search(self, query: str, user_id: str, top_k: int = 10, 
                        hybrid_search: bool = True, alpha: float = 0.5,
                        rerank: bool = True, rerank_model: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2',
                        rerank_factor: int = 4, 
                        use_bm25_first_pass: bool = True,
                        first_pass_k: int = 5) -> List[Document]:
        """
        Search for documents similar to a query, filtered by user_id.
        
        Combines dense vector search (semantic) with PostgreSQL full-text search (lexical)
        for improved accuracy when hybrid_search=True.
        
        Args:
            query: The search query
            user_id: The user ID to filter results by
            top_k: The number of top results to return (typically 3-5 for final results)
            hybrid_search: Whether to use hybrid search (both vector and text search)
            alpha: Weight factor for blending vector and text scores (0.0-1.0)
                  Higher values favor vector search, lower values favor text search
            rerank: Whether to apply cross-encoder reranking to improve result order
            rerank_model: Name of the cross-encoder model to use for reranking
            rerank_factor: Number of initial candidates to retrieve for reranking (as multiple of top_k)
                          Typically 3-4x the final top_k value
            use_bm25_first_pass: Whether to use BM25 for first-pass document retrieval
            first_pass_k: Number of documents to retrieve in the first pass
            
        Returns:
            A list of documents similar to the query
        """
        session = None
        try:
            session = self._Session()

            # First-Pass Document Retrieval using BM25 if enabled
            if use_bm25_first_pass:
                # Get all documents for this user
                all_docs = self.get_all_documents(user_id=user_id)
                
                # Initialize BM25 retriever
                bm25_retriever = BM25Retriever.from_documents(all_docs)
                
                # Get top documents using BM25
                first_pass_docs = bm25_retriever.get_relevant_documents(query)[:first_pass_k]
                
                # Extract document IDs from first pass results
                first_pass_doc_ids = set()
                for doc in first_pass_docs:
                    if 'document_id' in doc.metadata:
                        first_pass_doc_ids.add(doc.metadata['document_id'])
                
                logger.info(f"First-pass BM25 retrieved {len(first_pass_doc_ids)} documents")
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # For reranking, we retrieve more initial candidates
            initial_top_k = top_k * rerank_factor if rerank else top_k
            
            # Base query
            base_query = session.query(ChunkEmbedding).filter(
                ChunkEmbedding.user_id == user_id
            )
            
            # Filter by document IDs from first pass if BM25 was used
            if use_bm25_first_pass and first_pass_doc_ids:
                base_query = base_query.filter(
                    ChunkEmbedding.document_id.in_(first_pass_doc_ids)
                )
            
            if not hybrid_search:
                # Use vector search only
                results = base_query.order_by(
                    ChunkEmbedding.embedding.cosine_distance(query_embedding)
                ).limit(initial_top_k).all()
            else:
                # Hybrid search: combine vector similarity with text similarity
                from sqlalchemy import func, text, cast, Float
                
                # Convert the JSON 'page_content' field to text for full-text search
                content_extractor = func.jsonb_extract_path_text(ChunkEmbedding.data, 'page_content')
                
                # Create tsvector and tsquery for PostgreSQL full-text search
                ts_vector = func.to_tsvector('english', content_extractor)
                ts_query = func.plainto_tsquery('english', query)
                
                # Calculate text search rank using PostgreSQL ts_rank
                text_rank = func.ts_rank(ts_vector, ts_query)
                
                # Calculate vector similarity (cosine distance)
                vector_distance = ChunkEmbedding.embedding.cosine_distance(query_embedding)
                
                # Convert vector distance to a similarity score (1 - distance)
                vector_similarity = 1 - (vector_distance / 2.0)
                
                # Calculate the combined score with alpha as the weighting factor
                combined_score = (
                    alpha * vector_similarity.cast(Float) + 
                    (1 - alpha) * text_rank.cast(Float)
                )
                
                # Hybrid query that filters for text match and sorts by combined score
                results = base_query.filter(
                    ts_vector.op('@@')(ts_query)  # @@ is the text search match operator
                ).order_by(
                    combined_score.desc()  # Higher score is better
                ).limit(initial_top_k).all()
                
                # If we didn't get enough results with text matching,
                # fall back to pure vector search for the remaining slots
                if len(results) < initial_top_k:
                    remaining = initial_top_k - len(results)
                    # Get IDs of already retrieved results to exclude them
                    existing_ids = [r.id for r in results]
                    
                    # Pure vector search for remaining results
                    vector_results = base_query.filter(
                        ~ChunkEmbedding.id.in_(existing_ids)  # Exclude already retrieved docs
                    ).order_by(
                        ChunkEmbedding.embedding.cosine_distance(query_embedding)
                    ).limit(remaining).all()
                    
                    # Combine results
                    results.extend(vector_results)
            
            # Apply cross-encoder reranking if requested
            if rerank and results:
                results = self._rerank_with_cross_encoder(
                    query=query,
                    initial_results=results,
                    top_k=top_k,
                    model_name=rerank_model
                )
            elif len(results) > top_k:
                # If we retrieved more results than needed (for reranking) but didn't rerank,
                # trim to the requested top_k
                results = results[:top_k]
                
            # Convert results to LangChain documents and return
            return [result.to_langchain_doc() for result in results]
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

    def get_all_documents(self, user_id: str = None) -> List[Document]:
        """Get all documents from the store, optionally filtered by user_id."""
        session = None
        try:
            session = self._Session()
            query = session.query(ChunkEmbedding)
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(ChunkEmbedding.user_id == user_id)
                
            chunks = query.all()
            return [chunk.to_langchain_doc() for chunk in chunks]
        finally:
            if session:
                session.close()

    def delete_documents(self, uids: List[str], user_id: str = None) -> bool:
        """Delete documents from the store using raw SQL, optionally filtered by user_id."""
        session = None
        try:
            session = self._Session()
            # Build the base query
            query = "DELETE FROM chunks_embeddings WHERE id = ANY(:uids)"
            params = {"uids": uids}
            
            # Add user_id filter if provided
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
                
            session.execute(text(query), params)
            session.commit()
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
    
    # Optimize indexes (if not already created during initialization)
    pgvector.ensure_text_search_index()
    pgvector.create_vector_index(index_type='ivfflat', lists=10)  # Small list count for test data
    
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
    
