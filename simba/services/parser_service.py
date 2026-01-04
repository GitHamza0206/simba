"""Document parsing service using Unstructured."""

from io import BytesIO

from unstructured.partition.auto import partition

# MIME type to file extension mapping for unstructured
MIME_TO_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.ms-powerpoint": ".ppt",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/html": ".html",
    "text/csv": ".csv",
}


def parse_document(file_content: bytes, mime_type: str, filename: str) -> str:
    """Parse a document and extract text content.

    Args:
        file_content: Raw file content as bytes.
        mime_type: MIME type of the document.
        filename: Original filename (used for extension detection).

    Returns:
        Extracted text content as a single string.

    Raises:
        ValueError: If the file type is not supported.
    """
    # Get file extension from MIME type or filename
    ext = MIME_TO_EXT.get(mime_type)
    if not ext and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    if not ext:
        raise ValueError(f"Unsupported file type: {mime_type}")

    # Use unstructured's partition function
    # It automatically detects and handles different file types
    elements = partition(
        file=BytesIO(file_content),
        metadata_filename=filename,
    )

    # Combine all elements into a single text
    text_parts = []
    for element in elements:
        text = str(element)
        if text.strip():
            text_parts.append(text.strip())

    return "\n\n".join(text_parts)


def get_supported_mime_types() -> list[str]:
    """Get list of supported MIME types.

    Returns:
        List of supported MIME type strings.
    """
    return list(MIME_TO_EXT.keys())


def is_supported_mime_type(mime_type: str) -> bool:
    """Check if a MIME type is supported.

    Args:
        mime_type: MIME type to check.

    Returns:
        True if supported, False otherwise.
    """
    return mime_type in MIME_TO_EXT
