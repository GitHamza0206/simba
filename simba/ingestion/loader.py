import asyncio
from typing import List

from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)


class Loader:
    def __init__(self):
        self.SUPPORTED_EXTENSIONS = {
            ".md": UnstructuredMarkdownLoader,
            ".pdf": UnstructuredPDFLoader,
            ".pptx": UnstructuredPowerPointLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".docx": UnstructuredWordDocumentLoader,
            ".txt": TextLoader,
        }
        self.current_loader = None  # Track current loader

    @property
    def __name__(self):
        """Return the name of the current loader class"""
        return self.current_loader.__name__ if self.current_loader else None

    async def aload(self, file_path: str) -> List[Document]:
        file_extension = f".{file_path.split('.')[-1].lower()}"
        self.current_loader = self.SUPPORTED_EXTENSIONS[file_extension]
        return await asyncio.to_thread(lambda: self.current_loader(file_path=str(file_path)).load())
