from simba.parsing.base import BaseParser
from simba.models.simbadoc import SimbaDoc
from requests import post, RequestException
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IsolatedDoclingParser(BaseParser):
    def parse(self, document: SimbaDoc) -> SimbaDoc:
        # Update URL - check if this is the correct endpoint
        url = "http://172.16.9.144:6008/api/parse"  # Changed to include /api/ prefix
        
        try:
            # Open the file from the correct metadata path
            with open(document.metadata.file_path, "rb") as file:
                # Send the request with proper files parameter
                response = post(url, files={"file": file}, timeout=30)
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse the response
            parsed_data = response.json()
            logger.info(f"Successfully parsed document {document.id}")
            
            # Create a new SimbaDoc with the parsed data
            for chunk in parsed_data:
                chunk["id"] = str(uuid.uuid4())
                chunk["metadata"]["source"] = document.metadata.file_path

            document.metadata.parsing_status = "SUCCESS"
            document.metadata.parser = "isolated_docling"
            document.metadata.parsed_at = datetime.now()
            
            new_document = SimbaDoc(id=document.id, documents=parsed_data, metadata=document.metadata)
            return new_document
            
        except RequestException as e:
            # Handle request errors (404, connection problems, etc.)
            logger.error(f"Error connecting to parsing service: {str(e)}")
            logger.error(f"Response status: {getattr(e.response, 'status_code', 'Unknown')}")
            logger.error(f"Response content: {getattr(e.response, 'content', 'Unknown')}")
            
            # Update document status to reflect failure
            document.metadata.parsing_status = "FAILED"
            document.metadata.parser = "isolated_docling"
            document.metadata.parsed_at = datetime.now()
            return document
            
        except Exception as e:
            # Handle other errors (file not found, JSON parsing, etc.)
            logger.error(f"Error parsing document: {str(e)}")
            document.metadata.parsing_status = "FAILED"
            document.metadata.parser = "isolated_docling"
            document.metadata.parsed_at = datetime.now()
            return document
