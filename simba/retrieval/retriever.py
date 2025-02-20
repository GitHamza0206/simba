from simba.core.factories.vector_store_factory import VectorStoreFactory
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever


class Retriever:
    def __init__(self):
        self.store = VectorStoreFactory.get_vector_store()

    def as_retriever(self, **kwargs):
        return self.store.as_retriever(**kwargs)

    def as_ensemble_retriever(self):
        documents = self.store.get_documents()
        
        self.store.save()

        retriever = self.store.as_retriever(
            search_type="similarity",
            search_kwargs = {
                "k": 5
            }
        )
        keyword_retriever = BM25Retriever.from_documents(
            documents,
            preprocess_func=lambda text: text.lower()  # Simple preprocessing
        )
        return EnsembleRetriever(retrievers=[retriever, keyword_retriever], weights=[0.7, 0.3])