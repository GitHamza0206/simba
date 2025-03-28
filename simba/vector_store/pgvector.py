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
    
    def __init__(self, embedding_dim: int = 1536):
        """
        Initialize the vector store.
        
        Args:
            embedding_dim: Dimension of the embedding vectors
        """
        self.embedding_dim = embedding_dim
        
        # Initialize PostgresDB if not already initialized
        self.db = PostgresDB()
        self._Session = self.db._Session
    
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
            user_id = existing_doc.user_id
            
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
    
    def similarity_search(self, query: str, user_id: str, top_k: int = 10) -> List[Document]:
        """
        Search for documents similar to a query, filtered by user_id.
        
        Args:
            query: The search query
            user_id: The user ID to filter results by
            top_k: The number of top results to return
            
        Returns:
            A list of documents similar to the query
        """
        session = None
        try:
            session = self._Session()
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Perform vector similarity search using cosine distance, filtered by user_id
            results = session.query(ChunkEmbedding).filter(
                ChunkEmbedding.user_id == user_id
            ).order_by(
                ChunkEmbedding.embedding.cosine_distance(query_embedding)
            ).limit(top_k).all()
            
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

if __name__ == "__main__":
    pgvector = PGVectorStore()
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
            LangchainDocument(page_content="This is a test document for pgvector", metadata={"source": "test"})
        ],
        metadata=MetadataType(filename="test1.txt", type="text", enabled=True)
    )
    
    doc2 = SimbaDoc(
        id="test_doc_2",
        documents=[
            LangchainDocument(page_content="Another test document with different content", metadata={"source": "test"})
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
    
    # Search for similar documents
    print(f"\nSearching for 'test document'...")
    results = pgvector.similarity_search("test document", test_user_id)
    print(f"Found {len(results)} results")
    for doc in results:
        print(f"- {doc.page_content} (score: {doc.metadata.get('score', 'N/A')})")
    
    print(f"\nSearching for 'another document'...")
    results = pgvector.similarity_search("another document", test_user_id)
    print(f"Found {len(results)} results")
    for doc in results:
        print(f"- {doc.page_content} (score: {doc.metadata.get('score', 'N/A')})")
    
    print("\nTest completed successfully!")
    
