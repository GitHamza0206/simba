import logging
import os
from core.factories.embeddings_factory import get_embeddings
from core.config import settings
from langchain_community.vectorstores import FAISS, Chroma
from langchain.docstore.document import Document
import logging
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from typing import Optional, Union


logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.embeddings = get_embeddings()
        self._initialize_store()
    
    def _initialize_store(self):
        if settings.vector_store.provider == "faiss":
            self.store = self._initialize_faiss()
        elif settings.vector_store.provider == "chroma":
            self.store = self._initialize_chroma()
    
    def as_retriever(self, **kwargs) :
        return self.store.as_retriever(**kwargs)
    
    def save(self):
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
    
    

    def add_documents(self, documents: list[Document]) -> Union[list[Document], bool]:
        # Add documents to store
        try:
            for doc in documents:
                if self.chunk_in_store(doc.id):
                    print(f"Document {doc.id} already in store")
                    return False
                else:
                    print(f"Adding {doc.id} to store")
            
            self.store.add_documents(documents)
            self.save()
            return documents
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
        

    def count_documents(self):
        """Count documents in store."""
        if isinstance(self.store, FAISS):
            return len(self.store.docstore._dict)
        # For other vector stores that support len()
        return len(self.store)

    def delete_documents(self, uids: list[str]):
        # Delete documents from store
        try:
            self.store.delete(uids)
            self.save()
        except Exception as e:
            logger.error(f"Error deleting documents {uids}: {e}")
            raise e
        
    def clear_store(self):
        docstore = self.store.docstore
        index_to_docstore_id = self.store.index_to_docstore_id
        try:
            if len(index_to_docstore_id) == 0:
                raise ValueError("Store is already empty")
            # Retrieve all documents
            doc_ids = []
            for index, doc_id in index_to_docstore_id.items():
                document = docstore.search(doc_id)
                if document:
                    doc_ids.append(doc_id)
            
            return self.delete_documents(doc_ids)
        except Exception as e:
            logger.error(f"Error clearing store: {e}")
            raise e


    
    def chunk_in_store(self, chunk_id: str) -> bool:
        index_to_docstore_id = self.store.index_to_docstore_id
        return chunk_id in index_to_docstore_id.values()
    

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
        if os.path.exists(settings.paths.faiss_index_dir) and len(os.listdir(settings.paths.faiss_index_dir)) > 0:
            logging.info("Loading existing FAISS vector store")
            print("Loading existing FAISS vector store")
            store = FAISS.load_local(
                settings.paths.faiss_index_dir,
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
        else:
            logging.info("Initializing empty FAISS vector store with 'hello world'")
            print("Initializing empty FAISS vector store...")
            index = faiss.IndexFlatL2(len(self.embeddings.embed_query("hello world")))

            store = FAISS(
                embedding_function=self.embeddings,
                index=index,
                docstore= InMemoryDocstore(),
                index_to_docstore_id={}
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

def usage():
    store = VectorStoreService()
    print("Number of documents in store:", store.count_documents())
    
    


if __name__ == "__main__":
    usage()