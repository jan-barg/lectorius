"""Epub parsing utilities."""

import logging
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from lectorius_pipeline.errors import EpubParseError
from lectorius_pipeline.schemas import BookMeta

logger = logging.getLogger(__name__)


def parse_epub(epub_path: Path, book_id: str) -> tuple[str, BookMeta]:
    """
    Parse epub file and extract text content and metadata.

    Args:
        epub_path: Path to epub file
        book_id: Identifier for the book

    Returns:
        Tuple of (raw_text, book_metadata)

    Raises:
        EpubParseError: If epub cannot be parsed
    """
    try:
        book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
    except Exception as e:
        raise EpubParseError(f"Failed to parse epub: {e}") from e

    metadata = _extract_metadata(book, book_id)
    text = _extract_text(book)

    return text, metadata


def _extract_metadata(book: epub.EpubBook, book_id: str) -> BookMeta:
    """Extract metadata from epub."""
    title = _get_metadata_value(book, "title") or book_id
    author = _get_metadata_value(book, "creator")
    language = _get_metadata_value(book, "language") or "en"

    # Try to extract year from date
    date_str = _get_metadata_value(book, "date")
    year = None
    if date_str:
        try:
            year = int(date_str[:4])
        except (ValueError, IndexError):
            pass

    # Check for Gutenberg source
    source = None
    source_id = None
    identifier = _get_metadata_value(book, "identifier")
    if identifier and "gutenberg" in identifier.lower():
        source = "gutenberg"
        # Try to extract ID from identifier
        parts = identifier.split("/")
        if parts:
            source_id = parts[-1]

    return BookMeta(
        book_id=book_id,
        title=title,
        author=author,
        language=language[:2] if language else "en",  # normalize to 2-char code
        year=year,
        source=source,
        source_id=source_id,
    )


def _get_metadata_value(book: epub.EpubBook, key: str) -> str | None:
    """Get first metadata value for key."""
    values = book.get_metadata("DC", key)
    if values:
        value = values[0]
        if isinstance(value, tuple):
            return value[0] if value[0] else None
        return value if value else None
    return None


def _extract_text(book: epub.EpubBook) -> str:
    """Extract text from all spine documents in reading order."""
    texts: list[str] = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content()
        soup = BeautifulSoup(content, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Extract text
        text = soup.get_text(separator="\n")
        if text.strip():
            texts.append(text)

    return "\n\n".join(texts)
