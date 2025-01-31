from core.factories.database_factory import get_database

db = get_database()
def test_docling():
    from docling.document_converter import DocumentConverter
    from docling.chunking import HybridChunker
    from langchain_docling.loader import ExportType

    
    db = get_database()
    conv_res = DocumentConverter().convert("https://arxiv.org/pdf/2206.01062")
    doc = conv_res.document

    chunker = HybridChunker(tokenizer="BAAI/bge-small-en-v1.5")  # set tokenizer as needed
    chunk_iter = chunker.chunk(doc)

    print(chunk_iter)

def test_docling_langchain():
    from langchain_docling import DoclingLoader
    from docling.chunking import HybridChunker

    doc = db.get_document("d0b5fc22-3020-474c-9c32-b86fe51f66eb")
    loader = DoclingLoader(
        file_path=doc.metadata.file_path,
        chunker=HybridChunker(tokenizer="sentence-transformers/all-MiniLM-L6-v2"),

    )
    docs = loader.load()
    print(docs)
    
if __name__ == "__main__":
    test_docling_langchain()