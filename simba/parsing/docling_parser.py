import uuid
from datetime import datetime
from typing import List, Union

from docling.chunking import HybridChunker
from langchain_docling import DoclingLoader

from simba.core.config import settings
from simba.models.simbadoc import SimbaDoc
from simba.parsing.base import BaseParser


class DoclingParser(BaseParser):
    """
    A parser that uses Docling to chunk and parse documents.
    """

    def parse(self, document: SimbaDoc) -> Union[SimbaDoc, List[SimbaDoc]]:

        try:
            loader = DoclingLoader(
                file_path=document.metadata.file_path,
                chunker=HybridChunker(
                    tokenizer="sentence-transformers/all-MiniLM-L6-v2",
                    device=settings.embedding.device,
                ),
            )
            docs = loader.load()

            # Create new IDs for each parsed document
            for doc in docs:
                doc.id = str(uuid.uuid4())

            # Update metadata to reflect successful parsing
            document.metadata.parsing_status = "SUCCESS"
            document.metadata.parser = "docling"
            document.metadata.parsed_at = datetime.now()

            new_document = SimbaDoc(id=document.id, documents=docs, metadata=document.metadata)
            return new_document

        except Exception:
            document.metadata.parsing_status = "FAILED"
            # Optionally, log or rethrow the error here
            return document
