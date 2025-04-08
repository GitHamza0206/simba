from langchain.schema import Document as LangchainDocument
from simba.models.simbadoc import SimbaDoc, MetadataType
from simba.vector_store.pgvector import PGVectorStore
from simba.database.postgres import PostgresDB
from simba.auth.supabase_client import get_supabase_client
def test_bm25():
    # Initialize vector store
    pgvector = PGVectorStore(create_indexes=False)
    supabase = get_supabase_client()

    # Test user ID
    test_user_id = "test_user_bm25"

    
    # Create test documents with different content
    doc1 = SimbaDoc(
        id="bm25_doc_1",
        documents=[
            LangchainDocument(
                id="bm25_doc_1",
                page_content="Python is a high-level programming language known for its simplicity.",
                metadata={"source": "test", "document_id": "bm25_doc_1"}
            )
        ],
        metadata=MetadataType(filename="python.txt", type="text", enabled=True)
    )
    
    doc2 = SimbaDoc(
        id="bm25_doc_2",
        documents=[
            LangchainDocument(
                id="bm25_doc_2",
                page_content="JavaScript is a popular language for web development.",
                metadata={"source": "test", "document_id": "bm25_doc_2"}
            )
        ],
        metadata=MetadataType(filename="javascript.txt", type="text", enabled=True)
    )
    
    doc3 = SimbaDoc(
        id="bm25_doc_3",
        documents=[
            LangchainDocument(
                id="bm25_doc_3",
                page_content="Python frameworks like Django and Flask are used for web development.",
                metadata={"source": "test", "document_id": "bm25_doc_3"}
            )
        ],
        metadata=MetadataType(filename="python_web.txt", type="text", enabled=True)
    )
    
    # Insert documents into database and vector store
    db = PostgresDB()
    for doc in [doc1, doc2, doc3]:
        db.insert_document(doc, test_user_id)
        pgvector.add_documents(doc.documents, doc.id)
    
    print("\nTesting BM25 First Pass Retrieval...")
    print("=====================================")
    
    # Search query focused on Python
    query = "Python programming language"
    results = pgvector.similarity_search(
        query=query,
        user_id=test_user_id,
        top_k=3,
        hybrid_search=False,
        rerank=False,
        use_bm25_first_pass=True,
        first_pass_k=3
    )
    
    print(f"\nSearch Query: '{query}'")
    print("Retrieved Documents:")
    print("-----------------")
    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc.page_content}")

if __name__ == "__main__":
    test_bm25() 
    