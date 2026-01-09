"""Document parsing service with configurable backends.

Supports three backends (set via PARSER_BACKEND env var):
- mistral: Mistral OCR API (default, lightweight, requires MISTRAL_API_KEY)
- docling: Local parsing with Docling (heavy deps, install with `uv sync --extra docling`)
- unstructured: Unstructured API (requires UNSTRUCTURED_API_KEY, install with `uv sync --extra unstructured`)
"""

import base64
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from simba.core.config import settings

if TYPE_CHECKING:
    from docling.document_converter import DocumentConverter
    from mistralai import Mistral

logger = logging.getLogger(__name__)

# MIME types supported by each backend
MISTRAL_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/html": ".html",
}

DOCLING_MIME_TYPES = {
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

UNSTRUCTURED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/html": ".html",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "text/csv": ".csv",
    "application/xml": ".xml",
    "application/json": ".json",
}

# Text MIME types (passthrough, no parsing needed)
TEXT_MIME_TYPES = {"text/plain", "text/markdown", "text/html"}

# Lazy-loaded clients
_mistral_client: "Mistral | None" = None
_docling_converter: "DocumentConverter | None" = None


def _get_mime_types() -> dict[str, str]:
    """Get MIME types for the configured backend."""
    backend = settings.parser_backend.lower()
    if backend == "mistral":
        return MISTRAL_MIME_TYPES
    elif backend == "docling":
        return DOCLING_MIME_TYPES
    elif backend == "unstructured":
        return UNSTRUCTURED_MIME_TYPES
    else:
        raise ValueError(f"Unknown parser backend: {backend}")


def _get_mistral_client() -> "Mistral":
    """Get or create the Mistral client."""
    global _mistral_client
    if _mistral_client is None:
        from mistralai import Mistral

        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required for Mistral OCR backend")
        _mistral_client = Mistral(api_key=settings.mistral_api_key)
    return _mistral_client


def _get_docling_converter() -> "DocumentConverter":
    """Get or create the Docling converter."""
    global _docling_converter
    if _docling_converter is None:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as e:
            raise ImportError("Docling not installed. Install with: uv sync --extra docling") from e
        _docling_converter = DocumentConverter()
    return _docling_converter


def _parse_with_mistral(file_content: bytes, mime_type: str) -> str:
    """Parse document using Mistral OCR API."""
    client = _get_mistral_client()

    b64 = base64.b64encode(file_content).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": data_url},
    )

    parts = []
    for page in ocr_response.pages:
        if page.markdown:
            parts.append(page.markdown)

    return "\n\n".join(parts)


def _parse_with_docling(file_content: bytes, mime_type: str, filename: str) -> str:
    """Parse document using Docling."""
    converter = _get_docling_converter()

    ext = DOCLING_MIME_TYPES.get(mime_type)
    if not ext and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = Path(tmp.name)

    try:
        result = converter.convert(str(tmp_path))
        return result.document.export_to_markdown()
    finally:
        tmp_path.unlink(missing_ok=True)


def _parse_with_unstructured(file_content: bytes, _mime_type: str, filename: str) -> str:
    """Parse document using Unstructured API."""
    try:
        from unstructured_client import UnstructuredClient
        from unstructured_client.models import operations, shared
    except ImportError as e:
        raise ImportError(
            "Unstructured not installed. Install with: uv sync --extra unstructured"
        ) from e

    if not settings.unstructured_api_key:
        raise ValueError("UNSTRUCTURED_API_KEY is required for Unstructured backend")

    client = UnstructuredClient(
        api_key_auth=settings.unstructured_api_key,
        server_url=settings.unstructured_api_url,
    )

    req = operations.PartitionRequest(
        partition_parameters=shared.PartitionParameters(
            files=shared.Files(
                content=file_content,
                file_name=filename,
            ),
            strategy=shared.Strategy.AUTO,
        ),
    )

    resp = client.general.partition(request=req)
    elements = resp.elements or []

    # Combine elements into markdown
    parts = []
    for el in elements:
        if hasattr(el, "text") and el.text:
            parts.append(el.text)

    return "\n\n".join(parts)


def _parse_text(file_content: bytes) -> str:
    """Parse text files (passthrough)."""
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        return file_content.decode("latin-1")


def parse_document(file_content: bytes, mime_type: str, filename: str) -> str:
    """Parse a document and extract text content.

    Args:
        file_content: Raw file content as bytes.
        mime_type: MIME type of the document.
        filename: Original filename.

    Returns:
        Extracted text content as markdown string.

    Raises:
        ValueError: If the file type is not supported.
    """
    mime_types = _get_mime_types()
    if mime_type not in mime_types:
        raise ValueError(f"Unsupported file type: {mime_type}")

    # Text files - just decode
    if mime_type in TEXT_MIME_TYPES:
        logger.info(f"Parsing {filename} as text (passthrough)")
        return _parse_text(file_content)

    backend = settings.parser_backend.lower()
    logger.info(f"Parsing {filename} with {backend} backend")

    if backend == "mistral":
        return _parse_with_mistral(file_content, mime_type)
    elif backend == "docling":
        return _parse_with_docling(file_content, mime_type, filename)
    elif backend == "unstructured":
        return _parse_with_unstructured(file_content, mime_type, filename)
    else:
        raise ValueError(f"Unknown parser backend: {backend}")


def get_supported_mime_types() -> list[str]:
    """Get list of supported MIME types for the configured backend."""
    return list(_get_mime_types().keys())


def is_supported_mime_type(mime_type: str) -> bool:
    """Check if a MIME type is supported by the configured backend."""
    return mime_type in _get_mime_types()
