import os
import base64
import re
import json
from mistralai import Mistral
from simba.models.simbadoc import SimbaDoc
from typing import List, Union, Dict, Any
import logging
from simba.parsing.base import BaseParser
from langchain.schema import Document
from datetime import datetime

class MistralOCR(BaseParser):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("MISTRAL_API_KEY")
        
        if not self.api_key:
            logging.warning("MISTRAL_API_KEY environment variable not set. MistralOCR will not function.")
        
        self.client = Mistral(api_key=self.api_key)
    
    def debug_log_object(self, obj: Any, name: str = "object") -> None:
        """Log object details for debugging"""
        try:
            if hasattr(obj, '__dict__'):
                logging.info(f"{name} attributes: {list(obj.__dict__.keys())}")
            elif isinstance(obj, dict):
                logging.info(f"{name} keys: {list(obj.keys())}")
            elif isinstance(obj, list):
                logging.info(f"{name} is a list with {len(obj)} items")
                if len(obj) > 0:
                    self.debug_log_object(obj[0], f"{name}[0]")
            else:
                logging.info(f"{name} type: {type(obj)}")
        except Exception as e:
            logging.error(f"Error logging {name}: {str(e)}")
    
    def replace_images_in_markdown(self, markdown_str: str, images_dict: dict) -> str:
        """
        Replace image references in markdown with actual base64 data URIs.
        
        Args:
            markdown_str: Markdown string with image references
            images_dict: Dictionary mapping image IDs to base64 strings
            
        Returns:
            Updated markdown string with base64 image data
        """
        logging.info(f"Starting image replacement in markdown")
        logging.info(f"Found {len(images_dict)} images to replace")
        
        # Log the first few characters of each image data for debugging
        for img_id, img_data in images_dict.items():
            data_preview = img_data[:50] + "..." if len(img_data) > 50 else img_data
            logging.info(f"Image {img_id}: {data_preview}")
        
        # First, try exact replacement pattern from Mistral cookbook
        for img_id, base64_data_uri in images_dict.items():
            pattern = f"![{img_id}]({img_id})"
            if pattern in markdown_str:
                logging.info(f"Found exact match for pattern: {pattern}")
                markdown_str = markdown_str.replace(pattern, f"![{img_id}]({base64_data_uri})")
        
        # Check if we still have unreplaced images
        for img_id in images_dict.keys():
            if f"!{img_id}" in markdown_str or f"({img_id})" in markdown_str:
                logging.info(f"Found partial match for image: {img_id}, trying regex")
                # Try more flexible regex pattern
                pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
                
                def replace_func(match):
                    alt_text = match.group(1)
                    img_src = match.group(2)
                    
                    # If this is one of our images, replace it
                    if img_src in images_dict:
                        logging.info(f"Replacing {img_src} with base64 data")
                        return f'![{alt_text}]({images_dict[img_src]})'
                    return match.group(0)
                
                markdown_str = pattern.sub(replace_func, markdown_str)
        
        # Add HTML img tags as a fallback for any remaining unreplaced images
        for img_id, base64_data_uri in images_dict.items():
            if f"({img_id})" in markdown_str:
                logging.info(f"Adding HTML img tag for {img_id} as fallback")
                img_html = f'<img src="{base64_data_uri}" alt="{img_id}" style="max-width:100%; height:auto; margin:10px 0;" />'
                # Add the HTML tag at the end of the markdown
                markdown_str += f"\n\n{img_html}\n\n"
        
        return markdown_str

    def parse(self, document: SimbaDoc) -> Union[SimbaDoc, List[SimbaDoc]]:
        """
        Process a document using Mistral's OCR capabilities and update the SimbaDoc with extracted text.
        
        Workflow:
        1. If file_path is an HTTPS URL, use it directly
        2. If file_path is a local file, upload it to Mistral API and get a signed URL
        3. Process the document with Mistral OCR API
        4. Extract and structure the OCR results
        
        Args:
            document: A SimbaDoc object containing the document to process
            
        Returns:
            The updated SimbaDoc with OCR text content or a list of SimbaDoc objects if the document was split
        """
        if not self.api_key:
            logging.error("Cannot perform OCR: MISTRAL_API_KEY not set")
            return document
            
        uploaded_file_id = None
        
        try:
            file_path = document.metadata.file_path
            logging.info(f"Processing document: {file_path}")
            
            # Check if the file path is a URL starting with https
            if file_path.startswith("https://"):
                # If it's already a URL, use it directly
                document_data = {
                    "type": "document_url",
                    "document_url": file_path
                }
                logging.info(f"Using direct URL: {file_path}")
            else:
                # Upload file to Mistral
                try:
                    filename = os.path.basename(file_path)
                    logging.info(f"Uploading file: {filename}")
                    with open(file_path, "rb") as file_content:
                        uploaded_file = self.client.files.upload(
                            file={
                                "file_name": filename,
                                "content": file_content,
                            },
                            purpose="ocr"
                        )
                    
                    uploaded_file_id = uploaded_file.id
                    logging.info(f"Successfully uploaded file to Mistral with ID: {uploaded_file_id}")
                    
                    # Get signed URL for the uploaded file
                    signed_url = self.client.files.get_signed_url(file_id=uploaded_file_id)
                    logging.info(f"Got signed URL: {signed_url.url[:50]}...")
                    
                    document_data = {
                        "type": "document_url",
                        "document_url": signed_url.url
                    }
                except Exception as upload_error:
                    logging.error(f"Error uploading file to Mistral: {str(upload_error)}")
                    raise
            
            logging.info("Calling Mistral OCR API with include_image_base64=True")
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document=document_data,
                include_image_base64=True
            )
            
            logging.info("Received OCR response from Mistral")
            self.debug_log_object(ocr_response, "ocr_response")
            
            _documents = []
            # Extract the text content from the OCR response
            if ocr_response and hasattr(ocr_response, 'pages'):
                logging.info(f"OCR response has {len(ocr_response.pages)} pages")
                
                # Process each page from the OCR response
                for page_idx, page in enumerate(ocr_response.pages):
                    logging.info(f"Processing page {page_idx+1}")
                    self.debug_log_object(page, f"page_{page_idx+1}")
                    
                    # Extract text content (markdown)
                    page_content = ""
                    
                    if hasattr(page, 'markdown'):
                        page_content = page.markdown
                        logging.info(f"Page {page_idx+1} has markdown content of length {len(page_content)}")
                        
                        # Build image mapping dictionary
                        image_data = {}
                        if hasattr(page, 'images') and page.images:
                            logging.info(f"Page {page_idx+1} has {len(page.images)} images")
                            
                            for img_idx, img in enumerate(page.images):
                                self.debug_log_object(img, f"image_{page_idx+1}_{img_idx+1}")
                                
                                # Get the image ID
                                img_id = None
                                if hasattr(img, 'id'):
                                    img_id = img.id
                                    logging.info(f"Image {img_idx+1} has ID: {img_id}")
                                else:
                                    img_id = f"img-{img_idx}.jpeg"
                                    logging.info(f"Image {img_idx+1} has no ID, using generated ID: {img_id}")
                                
                                # Get the base64 data
                                if hasattr(img, 'image_base64'):
                                    image_data[img_id] = img.image_base64
                                    logging.info(f"Using image_base64 field for {img_id}")
                                elif hasattr(img, 'base64'):
                                    # Check if base64 already has the data URI prefix
                                    if img.base64.startswith('data:'):
                                        image_data[img_id] = img.base64
                                    else:
                                        image_data[img_id] = f"data:image/jpeg;base64,{img.base64}"
                                    logging.info(f"Using base64 field for {img_id}")
                        
                        # Replace image references with actual data URIs
                        if image_data:
                            logging.info(f"Replacing {len(image_data)} images in markdown")
                            original_content = page_content
                            page_content = self.replace_images_in_markdown(page_content, image_data)
                            
                            # Check if any replacements were made
                            if original_content == page_content:
                                logging.warning("No image replacements were made in markdown!")
                                
                                # Add a debug section to the markdown with image data
                                page_content += "\n\n## DEBUG: Images\n\n"
                                for img_id, img_data in image_data.items():
                                    page_content += f"Image ID: {img_id}\n\n"
                                    page_content += f'<img src="{img_data}" alt="{img_id}" style="max-width:100%;" />\n\n'
                    else:
                        logging.warning(f"Page {page_idx+1} has no markdown content")
                    
                    # Create langchain document with the processed content
                    langchain_document = Document(
                        page_content=page_content, 
                        metadata={"page_number": page.index if hasattr(page, 'index') else page_idx+1}
                    ) 
                    _documents.append(langchain_document)
                
                
            document.documents = _documents
            document.metadata.parser = "mistral_ocr"
            document.metadata.parsed_at = datetime.now()
            document.metadata.parsing_status = "SUCCESS"
            
            # Log what we found for debugging
            logging.info(f"Processed {len(_documents)} pages from document")
            for idx, doc in enumerate(_documents):
                has_images = "data:image" in doc.page_content
                logging.info(f"Page {idx+1}: Contains images: {has_images}")
                
                # Log a sample of the content
                content_sample = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                logging.info(f"Page {idx+1} content sample: {content_sample}")
            
            return document
            
        except Exception as e:
            logging.error(f"Error processing document with Mistral OCR: {str(e)}")
            # In case of error, return the original document
            document.metadata.parsing_status = "FAILED"
            return document
        finally:
            # Clean up the uploaded file
            if uploaded_file_id:
                try:
                    self.client.files.delete(file_id=uploaded_file_id)
                    logging.info(f"Deleted uploaded file with ID: {uploaded_file_id}")
                except Exception as delete_error:
                    logging.warning(f"Failed to delete uploaded file {uploaded_file_id}: {str(delete_error)}")


if __name__ == "__main__":
    from simba.core.factories.database_factory import get_database
    parser = MistralOCR()
    db = get_database()
    document = db.get_document("57081a14-34cd-47d1-9446-87d0bd2d27be")   
    parsed_document = parser.parse(document)
    print(parsed_document.documents)


