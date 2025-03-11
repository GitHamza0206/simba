import re
from typing import List

from langchain.schema import Document


def _clean_documents(documents: List[Document]) -> List[Document]:
    """
    Clean a list of documents by removing images and markdown base64 images.
    """
    return [_clean_document_text(doc) for doc in documents]


def _clean_document_text(document: Document) -> Document:
    """
    Clean a document by removing images and markdown base64 images.
    """
    document.page_content = _extract_text_remove_images(document.page_content)
    return document


def _extract_text_remove_images(text: str) -> str:
    """
    A simple function to extract text only and remove base64 image tags.

    Args:
        text (str): The input text which might contain base64 images

    Returns:
        str: Text with base64 images removed
    """

    # Remove HTML img tags with base64 content
    cleaned_text = re.sub(r'<img[^>]*src=["\']data:image[^"\']*["\'][^>]*>', "", text)

    # Remove markdown base64 images ![alt](data:image...)
    cleaned_text = re.sub(r"!\[.*?\]\(data:image[^)]*\)", "", cleaned_text)

    return cleaned_text
