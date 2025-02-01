import logging
import os
from core.factories.embeddings_factory import get_embeddings
from core.config import settings
from langchain_community.vectorstores import FAISS, Chroma
from langchain.docstore.document import Document
import logging
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from typing import Optional, Union, List
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.embeddings = get_embeddings()
        self._initialize_store()
    
    def _initialize_store(self):
        # Clear existing store when changing providers
        if hasattr(self, 'store'):
            del self.store
        
        if settings.vector_store.provider == "faiss":
            self.store = self._initialize_faiss()
        elif settings.vector_store.provider == "chroma":
            self.store = self._initialize_chroma()

    
    def as_retriever(self, **kwargs) :
        return self.store.as_retriever(**kwargs)
    
    def save(self):
        # Ensure directory exists before saving
        os.makedirs(settings.paths.faiss_index_dir, exist_ok=True)
        self.store.save_local(settings.paths.faiss_index_dir)

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by its ID"""
        try:
            docstore = self.store.docstore
            document = docstore.search(document_id)
            if isinstance(document, Document):
                return document
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None
    
    def update_document(self, document_id: str, newDocument: Document) -> bool:
        try:        
            if newDocument:
                newDocument.metadata["id"] = document_id
                self.delete_documents([document_id])
                self.add_documents([newDocument])
            return True
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            raise e

    def get_documents(self) -> list[Document]:
        docstore = self.store.docstore
        index_to_docstore_id = self.store.index_to_docstore_id

        # Retrieve all documents
        all_documents = []
        for index, doc_id in index_to_docstore_id.items():
            document = docstore.search(doc_id)
            if document:
                all_documents.append(document)
        
        return all_documents
    
    

    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents with proper synchronization"""
        try:
            for doc in documents:
                if self.chunk_in_store(doc.id):
                    print(f"Document {doc.id} already in store")
                    return False
                else:
                    print(f"Adding {doc.id} to store")
            
            self.store.add_documents(documents)
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise e

    def count_documents(self):
        """Count documents in store."""
        if isinstance(self.store, FAISS):
            return len(self.store.docstore._dict)
        # For other vector stores that support len()
        return len(self.store)

    def delete_documents(self, uids: list[str]) -> bool:
        """Delete documents and verify deletion"""
        try:
            
            
            self.store.delete(uids)
            self.save() 
            self.verify_store_sync()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise e
        
    def clear_store(self):
        """Clear all documents and reset the FAISS index"""
        try:
            # Get embedding dimension from existing index or create new
            if hasattr(self.store, 'index') and self.store.index is not None:
                dim = self.store.index.d
            else:
                dim = len(self.embeddings.embed_query("test"))

            # Reset FAISS index
            self.store.index = faiss.IndexFlatL2(dim)
            
            # Clear document store
            self.store.docstore._dict.clear()
            self.store.index_to_docstore_id.clear()
            
            # Save empty state
            self.save()
            logger.info("Vector store cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing store: {e}")
            raise e


    
    def chunk_in_store(self, chunk_id: str) -> bool:
        index_to_docstore_id = self.store.index_to_docstore_id
        return chunk_id in index_to_docstore_id.values()
    

    def get_document_ids(self) -> list[str]:
        index_to_docstore_id = self.store.index_to_docstore_id
        return list(index_to_docstore_id.values())  

    def search(self, query, **kwargs):
        # Search for similar documents
        return self.store.similarity_search(query, **kwargs)
    
    def search_with_filters(self, query, **kwargs):
        # Search for similar documents with filters
        return self.store.similarity_search_with_score(query, **kwargs)    

    async def asearch_with_filters(self, query, **kwargs):
        # Search for similar documents with filters
        return await self.store.asearch_with_filters(query, **kwargs)    

   

    def _initialize_faiss(self):
        # Get actual embedding dimension from the model
        try:
            # Try to get dimension from HuggingFace embeddings
            if hasattr(self.embeddings, 'client') and hasattr(self.embeddings.client, 'dimension'):
                embedding_dim = self.embeddings.client.dimension
            elif hasattr(self.embeddings, 'model') and hasattr(self.embeddings.model, 'config'):
                embedding_dim = self.embeddings.model.config.hidden_size
            else:
                # Fallback for other embedding types: compute dimension from a test embedding
                embedding_dim = len(self.embeddings.embed_query("test"))
            
            logger.info(f"Using embedding dimension: {embedding_dim}")
        except Exception as e:
            logger.error(f"Error determining embedding dimension: {e}")
            # Fallback to computing dimension
            embedding_dim = len(self.embeddings.embed_query("test"))
            logger.info(f"Fallback: Using computed embedding dimension: {embedding_dim}")
        
        if os.path.exists(settings.paths.faiss_index_dir) and len(os.listdir(settings.paths.faiss_index_dir)) > 0:
            logging.info("Loading existing FAISS vector store")
            store = FAISS.load_local(
                settings.paths.faiss_index_dir,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            # Verify dimension match
            if store.index.d != embedding_dim:
                raise ValueError(f"Embedding dimension mismatch: Index has {store.index.d}D vs Model has {embedding_dim}D")
        else:
            logging.info(f"Initializing new FAISS index with dimension {embedding_dim}")
            index = faiss.IndexFlatL2(embedding_dim)
            store = FAISS(
                embedding_function=self.embeddings,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={},
            )
            store.save_local(settings.paths.faiss_index_dir)
        return store
    
    def _initialize_chroma(self, documents=None):
        logging.info("Initializing empty Chroma vector store with hello world")
        store = Chroma.from_documents(
            documents=documents or [Document(page_content="hello world")],
            embedding=self.embeddings,
            allow_dangerous_deserialization=True
        )
        store.save_local(settings.paths.faiss_index_dir)
        return store

    def verify_store_sync(self) -> bool:
        """
        Verify synchronization between FAISS index and document store
        Returns: bool indicating if stores are in sync
        """
        try:
            # Get counts
            faiss_count = self.store.index.ntotal
            docstore_count = len(self.store.docstore._dict)
            index_map_count = len(self.store.index_to_docstore_id)
            
            # Check all counts match
            counts_match = (faiss_count == docstore_count == index_map_count)
            
            # Verify all mapped IDs exist in docstore
            ids_exist = all(
                self.store.docstore._dict.get(doc_id) is not None 
                for doc_id in self.store.index_to_docstore_id.values()
            )
            
            if not counts_match:
                print(f"Count mismatch: FAISS={faiss_count}, "
                            f"Docstore={docstore_count}, "
                            f"Index Map={index_map_count}")
            
            return counts_match and ids_exist

        except Exception as e:
            logger.error(f"Error verifying store sync: {e}")
            return False

def usage():
    store = VectorStoreService()
    print(store.embeddings)
    
    


if __name__ == "__main__":
    usage()