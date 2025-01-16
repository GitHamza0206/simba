import subprocess
import os
import logging
from pathlib import Path
import shlex
from pydantic import BaseModel
from langchain.schema import Document
from services.vector_store_service import VectorStoreService
logger = logging.getLogger(__name__)



class ParserService:
    SUPPORTED_PARSERS = [
        "markitdown"
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
                    timeout=30
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
        else:
            raise ValueError(f"Unsupported parser: {parser}")
