import asyncio
import logging
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain_community.document_loaders import (
    CSVLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)

logger = logging.getLogger(__name__)


class Loader:
    def __init__(self):
        self.SUPPORTED_EXTENSIONS = {
            ".md": UnstructuredMarkdownLoader,
            ".pdf": UnstructuredPDFLoader,
            ".pptx": UnstructuredPowerPointLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".docx": UnstructuredWordDocumentLoader,
            ".txt": TextLoader,
            ".png": UnstructuredImageLoader,
            ".jpg": UnstructuredImageLoader,
            ".jpeg": UnstructuredImageLoader,
            ".gif": UnstructuredImageLoader,
            ".bmp": UnstructuredImageLoader,
            ".tiff": UnstructuredImageLoader,
            ".ico": UnstructuredImageLoader,
            ".csv": CSVLoader,
            ".doc": UnstructuredWordDocumentLoader,
            ".xls": UnstructuredExcelLoader,
            ".ppt": UnstructuredPowerPointLoader,
            ".rtf": UnstructuredWordDocumentLoader,
            ".odt": UnstructuredWordDocumentLoader,
            ".ods": UnstructuredExcelLoader,
            ".odp": UnstructuredPowerPointLoader,
            ".odg": UnstructuredImageLoader,
            ".odc": UnstructuredImageLoader,
        }
        self.current_loader = None  # Track current loader

    @property
    def __name__(self):
        """Return the name of the current loader class"""
        return self.current_loader.__name__ if self.current_loader else None

    async def aload(self, file_path: str) -> List[Document]:
        """
        Asynchronously load a document from a file path

        Args:
            file_path: Path to the file to load

        Returns:
            List[Document]: Loaded document chunks

        Raises:
            ValueError: If file_path is None or invalid
            FileNotFoundError: If the file does not exist
            KeyError: If the file extension is not supported
        """
        # Validate file_path
        if file_path is None or file_path == "None" or file_path == "":
            raise ValueError(f"Invalid file path: {file_path}")

        # Ensure file exists
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension and validate
        try:
            file_extension = f".{file_path.split('.')[-1].lower()}"
            if file_extension not in self.SUPPORTED_EXTENSIONS:
                raise KeyError(f"Unsupported file extension: {file_extension}")

            self.current_loader = self.SUPPORTED_EXTENSIONS[file_extension]
        except Exception as e:
            logger.error(f"Error determining file extension for {file_path}: {str(e)}")
            raise

        # Load file with appropriate loader
        try:
            return await asyncio.to_thread(
                lambda: self.current_loader(file_path=str(file_path)).load()
            )
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise
