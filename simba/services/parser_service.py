"""Document parsing service using Docling."""

import tempfile
from pathlib import Path

from docling.document_converter import DocumentConverter

# MIME type to file extension mapping
MIME_TO_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/html": ".html",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "text/asciidoc": ".adoc",
}

# Initialize converter once (lazy loading on first use)
_converter: DocumentConverter | None = None


def _get_converter() -> DocumentConverter:
    """Get or create the document converter instance."""
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter


def parse_document(file_content: bytes, mime_type: str, filename: str) -> str:
    """Parse a document and extract text content using Docling.

    Args:
        file_content: Raw file content as bytes.
        mime_type: MIME type of the document.
        filename: Original filename (used for extension detection).

    Returns:
        Extracted text content as markdown string.

    Raises:
        ValueError: If the file type is not supported.
    """
    # Get file extension from MIME type or filename
    ext = MIME_TO_EXT.get(mime_type)
    if not ext and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    if not ext:
        raise ValueError(f"Unsupported file type: {mime_type}")

    # Docling requires a file path, so write to a temp file
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = Path(tmp.name)

    try:
        converter = _get_converter()
        result = converter.convert(str(tmp_path))
        return result.document.export_to_markdown()
    finally:
        tmp_path.unlink(missing_ok=True)


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
