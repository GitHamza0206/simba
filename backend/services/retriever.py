from services.vector_store_service import VectorStoreService
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

class Retriever:
    def __init__(self):
        self.store = VectorStoreService()

    def as_retriever(self, **kwargs):
        return self.store.as_retriever(**kwargs)

    def as_ensemble_retriever(self):
        documents = self.store.get_documents()

        retriever = self.store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs = {
                "score_threshold": 0.7,
                "k": 5
            }
        )
        keyword_retriever  = BM25Retriever.from_documents(
            documents,
            preprocess_func=lambda text: text.lower()  # Simple preprocessing
        )
        return EnsembleRetriever(retrievers=[retriever, keyword_retriever], weights=[0.7, 0.3])