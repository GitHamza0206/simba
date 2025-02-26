import logging
import os

import faiss
from langchain.schema import Document
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.faiss import FAISS

from simba.core.config import settings
from simba.core.factories.embeddings_factory import get_embeddings
from simba.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    _instance = None
    _initialized = False
    _vector_store = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_store()
            self._initialized = True

    def _initialize_store(self):
        embeddings = get_embeddings()
        if settings.vector_store.provider == "faiss":
            self._vector_store = self._initialize_faiss(embeddings)
        elif settings.vector_store.provider == "chroma":
            self._vector_store = self._initialize_chroma(embeddings)
        else:
            raise ValueError(f"Unsupported vector store provider: {settings.vector_store.provider}")

    def _initialize_faiss(self, embeddings):

        # Get actual embedding dimension from the model
        try:
            # Try to get dimension from HuggingFace embeddings
            if hasattr(embeddings, "client") and hasattr(embeddings.client, "dimension"):
                embedding_dim = embeddings.client.dimension
            elif hasattr(embeddings, "model") and hasattr(embeddings.model, "config"):
                embedding_dim = embeddings.model.config.hidden_size
            else:
                # Fallback for other embedding types: compute dimension from a test embedding
                embedding_dim = len(embeddings.embed_query("test"))

            logger.info(f"Using embedding dimension: {embedding_dim}")
        except Exception as e:
            logger.error(f"Error determining embedding dimension: {e}")
            # Fallback to computing dimension
            embedding_dim = len(embeddings.embed_query("test"))
            logger.info(f"Fallback: Using computed embedding dimension: {embedding_dim}")

        if (
            os.path.exists(settings.paths.faiss_index_dir)
            and len(os.listdir(settings.paths.faiss_index_dir)) > 0
        ):
            logging.info("Loading existing FAISS vector store")
            store = FAISS.load_local(
                settings.paths.faiss_index_dir,
                embeddings,
                allow_dangerous_deserialization=True,
            )
            # Verify dimension match
            if store.index.d != embedding_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: Index has {store.index.d}D vs Model has {embedding_dim}D"
                )
        else:
            logging.info(f"Initializing new FAISS index with dimension {embedding_dim}")
            index = faiss.IndexFlatL2(embedding_dim)
            store = FAISS(
                embedding_function=embeddings,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={},
            )
            store.save_local(settings.paths.faiss_index_dir)
        return VectorStoreService(store=store, embeddings=embeddings)

    def _initialize_chroma(self, embeddings):
        logging.info("Initializing Chroma vector store")

        try:
            # Ensure embeddings are initialized
            if embeddings is None:
                raise ValueError("Embeddings must be provided for Chroma initialization")

            # Ensure directory exists
            os.makedirs(settings.paths.vector_store_dir, exist_ok=True)

            # Try to load existing store first
            try:
                logging.info("Attempting to load existing Chroma store")
                store = Chroma(
                    persist_directory=str(settings.paths.vector_store_dir),
                    embedding_function=embeddings,
                    collection_name=settings.vector_store.collection_name,
                )
                # Test the store
                store.similarity_search("test", k=1)
                logging.info("Successfully loaded existing Chroma store")
            except Exception as e:
                logging.info(f"Creating new Chroma store: {str(e)}")
                # Initialize with a test document
                store = Chroma.from_documents(
                    documents=[Document(page_content="test", metadata={})],
                    embedding_function=embeddings,
                    persist_directory=str(settings.paths.vector_store_dir),
                    collection_name=settings.vector_store.collection_name,
                )
                store.persist()
                logging.info("Successfully created new Chroma store")

            return VectorStoreService(store=store, embeddings=embeddings)

        except Exception as e:
            logger.error(f"Error initializing Chroma store: {e}", exc_info=True)
            raise ValueError(f"Failed to initialize Chroma vector store: {str(e)}")

    @classmethod
    def get_vector_store(cls) -> VectorStoreService:
        return cls()._vector_store

    @classmethod
    def reset(cls):
        """For testing purposes only"""
        cls._instance = None
        cls._initialized = False
