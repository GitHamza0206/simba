import logging
import os
from typing import Dict, List, Optional, Union

import numpy as np
from mistralai import Mistral

from simba.core.config import settings


class MultimodalEmbedder:
    """
    Generates and manages embeddings for multimodal content (text and images).
    This class focuses exclusively on embedding generation and storage,
    separate from the chunking logic.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the multimodal embedder.
        
        Args:
            api_key: Mistral API key for generating embeddings (optional, will use environment variable if not provided)
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        
        if not self.api_key:
            logging.warning(
                "MISTRAL_API_KEY not set. MultimodalEmbedder will not function properly."
            )
            self.client = None
        else:
            self.client = Mistral(api_key=self.api_key)
            
        # Dictionary to store embeddings
        self.embeddings_cache = {}
    
    def generate_image_embeddings(
        self, 
        image_chunks: List[str], 
        model_name: str = "mistral-embed",
        use_cache: bool = True
    ) -> Dict[str, List[float]]:
        """
        Generate embeddings for image chunks.
        
        Args:
            image_chunks: List of image data strings (typically base64-encoded)
            model_name: Name of the embedding model to use (default: "mistral-embed")
            use_cache: Whether to use cached embeddings (default: True)
            
        Returns:
            Dictionary mapping image data to their embedding vectors
        """
        if not self.client:
            logging.error("Cannot generate embeddings: Mistral API client not initialized")
            return {}
            
        if not image_chunks:
            logging.info("No image chunks to embed")
            return {}
            
        embeddings = {}
        logging.info(f"Generating multimodal embeddings for {len(image_chunks)} images")
        
        try:
            for i, img_data in enumerate(image_chunks):
                # If using cache and we already have this embedding, reuse it
                if use_cache and img_data in self.embeddings_cache:
                    embeddings[img_data] = self.embeddings_cache[img_data]
                    logging.info(f"Using cached embedding for image {i+1}")
                    continue
                
                logging.info(f"Processing image {i+1}/{len(image_chunks)}")
                
                # Check if the image is in base64 format with data URI prefix
                if img_data.startswith("data:image"):
                    # Extract the base64 content after the comma
                    try:
                        # Format is typically: data:image/jpeg;base64,/9j/...
                        base64_content = img_data.split(",", 1)[1]
                    except IndexError:
                        logging.warning(f"Could not extract base64 content from image data URI")
                        continue
                elif img_data.startswith("/9j/"):
                    # Already in base64 format without prefix
                    base64_content = img_data
                else:
                    logging.warning(f"Image data is not in recognized base64 format, skipping")
                    continue
                
                try:
                    # Generate embedding using Mistral API
                    embedding_response = self.client.embeddings.create(
                        model=model_name,
                        input=[
                            {
                                "type": "image_base64",
                                "image_base64": {
                                    "data": base64_content,
                                    "mime_type": "image/jpeg"  # Assuming JPEG format
                                }
                            }
                        ]
                    )
                    
                    # Extract the embedding vector
                    if embedding_response and hasattr(embedding_response, "data") and embedding_response.data:
                        vector = embedding_response.data[0].embedding
                        embeddings[img_data] = vector
                        # Store in cache
                        self.embeddings_cache[img_data] = vector
                        logging.info(f"Successfully generated embedding for image {i+1}")
                    else:
                        logging.warning(f"Failed to get embedding for image {i+1}: Empty response")
                        
                except Exception as e:
                    logging.error(f"Error generating embedding for image {i+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error in multimodal embedding process: {str(e)}")
            
        logging.info(f"Generated embeddings for {len(embeddings)}/{len(image_chunks)} images")
        return embeddings
    
    def generate_text_embeddings(
        self, 
        text_chunks: List[str], 
        model_name: str = "mistral-embed",
        use_cache: bool = True
    ) -> Dict[str, List[float]]:
        """
        Generate embeddings for text chunks.
        
        Args:
            text_chunks: List of text strings to embed
            model_name: Name of the embedding model to use (default: "mistral-embed")
            use_cache: Whether to use cached embeddings (default: True)
            
        Returns:
            Dictionary mapping text to their embedding vectors
        """
        if not self.client:
            logging.error("Cannot generate embeddings: Mistral API client not initialized")
            return {}
            
        if not text_chunks:
            logging.info("No text chunks to embed")
            return {}
            
        embeddings = {}
        logging.info(f"Generating embeddings for {len(text_chunks)} text chunks")
        
        try:
            # Process text chunks in batches to be more efficient
            batch_size = 32  # Adjust based on API limits and performance
            for i in range(0, len(text_chunks), batch_size):
                batch = text_chunks[i:i+batch_size]
                
                # Filter out texts we already have in cache if using cache
                if use_cache:
                    to_embed = [text for text in batch if text not in self.embeddings_cache]
                    # Add cached embeddings directly
                    for text in batch:
                        if text in self.embeddings_cache:
                            embeddings[text] = self.embeddings_cache[text]
                else:
                    to_embed = batch
                
                if not to_embed:
                    logging.info(f"All texts in batch {i//batch_size + 1} already cached")
                    continue
                
                logging.info(f"Embedding batch {i//batch_size + 1} with {len(to_embed)} texts")
                
                try:
                    # Generate embeddings using Mistral API
                    embedding_response = self.client.embeddings.create(
                        model=model_name,
                        input=to_embed
                    )
                    
                    # Extract the embedding vectors
                    if embedding_response and hasattr(embedding_response, "data"):
                        for j, data in enumerate(embedding_response.data):
                            if hasattr(data, "embedding"):
                                text = to_embed[j]
                                vector = data.embedding
                                embeddings[text] = vector
                                # Store in cache
                                self.embeddings_cache[text] = vector
                    else:
                        logging.warning(f"Failed to get embeddings for batch {i//batch_size + 1}: Empty response")
                        
                except Exception as e:
                    logging.error(f"Error generating embeddings for batch {i//batch_size + 1}: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error in text embedding process: {str(e)}")
            
        logging.info(f"Generated embeddings for {len(embeddings)}/{len(text_chunks)} text chunks")
        return embeddings
    
    def save_embeddings_to_file(self, path: str) -> bool:
        """
        Save all cached embeddings to a file.
        
        Args:
            path: Path to save the embeddings to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import pickle
            with open(path, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            logging.info(f"Saved {len(self.embeddings_cache)} embeddings to {path}")
            return True
        except Exception as e:
            logging.error(f"Error saving embeddings to {path}: {str(e)}")
            return False
    
    def load_embeddings_from_file(self, path: str) -> bool:
        """
        Load embeddings from a file into the cache.
        
        Args:
            path: Path to load the embeddings from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import pickle
            with open(path, 'rb') as f:
                loaded_cache = pickle.load(f)
            self.embeddings_cache.update(loaded_cache)
            logging.info(f"Loaded {len(loaded_cache)} embeddings from {path}")
            return True
        except Exception as e:
            logging.error(f"Error loading embeddings from {path}: {str(e)}")
            return False
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.embeddings_cache = {}
        logging.info("Cleared embedding cache") 