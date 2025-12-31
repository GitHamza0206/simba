"""Text chunking service using LangChain."""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""

    content: str
    position: int  # Position in the original document (0-indexed)
    start_char: int  # Starting character position
    end_char: int  # Ending character position


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Chunk]:
    """Split text into chunks with overlap.

    Args:
        text: The text to split.
        chunk_size: Maximum size of each chunk in characters.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of Chunk objects with content and metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    # Use create_documents to get metadata about positions
    docs = splitter.create_documents([text])

    chunks = []
    current_pos = 0

    for i, doc in enumerate(docs):
        content = doc.page_content

        # Find the actual position of this chunk in the original text
        start_char = text.find(content, current_pos)
        if start_char == -1:
            # Fallback if exact match not found
            start_char = current_pos

        end_char = start_char + len(content)

        chunks.append(
            Chunk(
                content=content,
                position=i,
                start_char=start_char,
                end_char=end_char,
            )
        )

        # Update position for next search (account for overlap)
        current_pos = max(start_char + 1, end_char - chunk_overlap)

    return chunks


def chunk_text_simple(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[str]:
    """Split text into chunks (simple version returning just strings).

    Args:
        text: The text to split.
        chunk_size: Maximum size of each chunk in characters.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of chunk strings.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    return splitter.split_text(text)
