from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    PyMuPDFLoader,
    PyPDFLoader,

)


SUPPORTED_EXTENSIONS = {
        ".md": UnstructuredMarkdownLoader,
        ".pdf": PyPDFLoader,
        ".pptx": UnstructuredPowerPointLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".docx": UnstructuredWordDocumentLoader,
        ".txt": TextLoader
    }