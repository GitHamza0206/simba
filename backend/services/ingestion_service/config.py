from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader,
    TextLoader
)

SUPPORTED_EXTENSIONS = {
        ".md": UnstructuredMarkdownLoader,
        ".pdf": UnstructuredPDFLoader,
        ".pptx": UnstructuredPowerPointLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".docx": UnstructuredWordDocumentLoader,
        ".txt": TextLoader
    }