from services.vector_store_service import VectorStoreService
from langchain.docstore.document import Document
store = VectorStoreService()

def test_in_database():
    print(store.chunk_in_store("df62cca4-8e53-497e-875e-3af02cba6c0f"))

def test_store_sync():
    store.verify_store_sync()

if __name__ == "__main__":
    test_in_database()