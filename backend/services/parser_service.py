import subprocess
import os
import logging
from pathlib import Path
import shlex
from typing import List, Union
from pydantic import BaseModel
from langchain.schema import Document
from models.simbadoc import SimbaDoc
from datetime import datetime
import torch

logger = logging.getLogger(__name__)

from langchain_docling import DoclingLoader
from docling.chunking import HybridChunker
from langchain_docling.loader import ExportType
from core.config import settings

class ParserService:
    SUPPORTED_PARSERS = [
        "markitdown",
        "docling"
    ]

    def __init__(self, device: str = None, force_cpu: bool = False):
        """Initialize parser service with specified device
        
        Args:
            device: Device to use ('cpu', 'cuda', 'mps', or None for auto-detect)
            force_cpu: If True, always use CPU regardless of device parameter
        """
        # Check environment variable first
        env_device = os.environ.get("PYTORCH_DEVICE")
        if env_device:
            self.device = env_device
            logger.info(f"Using device from environment: {self.device}")
        elif force_cpu:
            self.device = 'cpu'
            logger.info("Forcing CPU usage")
        else:
            if device is None:
                # Auto-detect best available device
                if torch.backends.mps.is_available():
                    device = 'mps'
                elif torch.cuda.is_available():
                    device = 'cuda'
                else:
                    device = 'cpu'
            self.device = device
            
        # Ensure PyTorch uses the selected device
        if self.device == 'cpu':
            torch.set_default_device('cpu')
        elif self.device == 'mps' and torch.backends.mps.is_available():
            torch.device('mps')
        elif self.device == 'cuda' and torch.cuda.is_available():
            torch.device('cuda')
            
        logger.info(f"Initialized ParserService with device: {self.device}")

    def get_parsers(self):
        return self.SUPPORTED_PARSERS

    def parse_document(self, document: SimbaDoc, parser: str) -> Union[SimbaDoc, List[SimbaDoc]]:
        """Return either single doc or list of docs"""
        if parser == "docling":
            # Returns list of split documents

            return self._parse_docling(document)
        else:
            # Return single modified document
            return self._parse_markitdown(document)

    def _parse_markitdown(self, document: SimbaDoc) -> str:
        """Parse markitdown and return content string"""
        document.id = "PARSER_TEST"
        return document

    def _parse_docling(self, document: SimbaDoc) -> List[SimbaDoc]:
        """Return list of chunked documents"""
        try:
            loader = DoclingLoader(
                file_path=document.metadata.file_path,
                chunker=HybridChunker(
                    tokenizer="sentence-transformers/all-MiniLM-L6-v2",
                    device=self.device
                ),
            )
            docs = loader.load()

            
            document.metadata.parsing_status = "SUCCESS"
            document.metadata.parser = "docling"
            document.metadata.parsed_at = datetime.now()

            doc = SimbaDoc(
                    id=document.id,
                    documents=docs,
                    metadata=document.metadata
                )
            
            return doc 
        
        except Exception as e:
            document.metadata.parsing_status = "FAILED"
            return document
        

        
        
