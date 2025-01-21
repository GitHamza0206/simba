import subprocess
import os
import logging
from pathlib import Path
import shlex
from pydantic import BaseModel
from langchain.schema import Document
from services.vector_store_service import VectorStoreService
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

    def get_parsers(self):
        return self.SUPPORTED_PARSERS

    def parse_document(self, document: Document, parser: str)-> Document:
        file_path = document.metadata.get('file_path')
        if parser == "markitdown":
            try:
                logger.info(f"Starting to parse document: {file_path}")
                # Ensure file exists
                if not os.path.exists(file_path):
                    raise ValueError(f"File not found: {file_path}")
                
                

                # Create output path with .md extension
                output_path = os.path.splitext(file_path)[0] + '.md'
                
                # Properly escape the file path for shell
                escaped_path = shlex.quote(file_path)
                escaped_output = shlex.quote(output_path)
                
                # Build command using input redirection and output redirection
                command = f"markitdown < {escaped_path} > {escaped_output}"
                logger.info(f"Executing command: {command}")
                
                # Execute markitdown command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                # Log the command output
                logger.info(f"Command stdout: {result.stdout}")
                logger.info(f"Command stderr: {result.stderr}")
                
                if result.returncode != 0:
                    logger.error(f"Markitdown failed with return code {result.returncode}")
                    raise ValueError(f"Markitdown failed: {result.stderr}")
                
                # Check if output file exists and read it
                if os.path.exists(output_path):
                    with open(output_path, 'r') as f:
                        content = f.read()
                        document.page_content = content
                        document.metadata["filename"] = os.path.basename(output_path)
                        document.metadata["file_path"] = output_path

                        document.metadata["parser"] = "markitdown"
                        f.close()

                        return document
                
                else:
                    raise ValueError("Output file was not created")
                
            except subprocess.TimeoutExpired:
                logger.error("Markitdown command timed out")
                raise ValueError("Parser timed out after 30 seconds")
            except Exception as e:
                logger.error(f"Error parsing document with markitdown: {str(e)}")
                raise ValueError(f"Parser error: {str(e)}")
        elif parser == "docling":
            from docling.document_converter import DocumentConverter

            try:
                logger.info(f"Starting to parse document: {file_path}")
                # Replace file extension with .md
                output_path = os.path.splitext(file_path)[0] + '.md'
                # EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

                # loader = DoclingLoader(
                #         file_path=file_path,
                #         export_type=ExportType.MARKDOWN,
                #         chunker=HybridChunker(tokenizer=EMBED_MODEL_ID),
                #     )

                # docs = loader.load()

                # converter = DocumentConverter()
                # result = converter.convert(file_path)
                # page_content = result.document.export_to_markdown()
                if not os.path.exists(file_path):
                    raise ValueError(f"File not found: {file_path}")
                
                output_folder_path = settings.paths.upload_dir
                
                # Properly escape the file path for shell
                escaped_path = shlex.quote(file_path)
                escaped_output = shlex.quote(output_path)
                
                # Build command using input redirection and output redirection
                command = f"docling {escaped_path} --output {output_folder_path}"
                logger.info(f"Executing command: {command}")
                
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode != 0:
                    logger.error(f"docling failed with return code {result.returncode}")
                    raise ValueError(f"docling failed: {result.stderr}")
                
                # Check if output file exists and read it
                if os.path.exists(output_path):
                    with open(output_path, 'r') as f:
                        content = f.read()
                        document.page_content = content
                        document.metadata["filename"] = os.path.basename(output_path)
                        document.metadata["file_path"] = output_path
                        document.metadata["parser"] = "docling"
                        f.close()

                        return document
                
                else:
                    raise ValueError("Output file was not created")


            
            

            except Exception as e:
                logger.error(f"Error parsing document with docling: {str(e)}")
                raise ValueError(f"Parser error: {str(e)}")
        else:
            raise ValueError(f"Unsupported parser: {parser}")
