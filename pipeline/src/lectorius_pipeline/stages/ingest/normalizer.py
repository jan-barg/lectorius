"""Text normalization utilities."""

import logging
import re

logger = logging.getLogger(__name__)

# Gutenberg markers
GUTENBERG_START_MARKERS = [
    r"\*\*\*\s*START OF THE PROJECT GUTENBERG EBOOK",
    r"\*\*\*\s*START OF THIS PROJECT GUTENBERG EBOOK",
]

GUTENBERG_END_MARKERS = [
    r"\*\*\*\s*END OF THE PROJECT GUTENBERG EBOOK",
    r"\*\*\*\s*END OF THIS PROJECT GUTENBERG EBOOK",
]

# Page artifacts
PAGE_NUMBER_PATTERN = re.compile(r"^\s*\d{1,4}\s*$")
ROMAN_NUMERAL_PATTERN = re.compile(r"^\s*[ivxlcdmIVXLCDM]{1,8}\s*$")

# TOC patterns
TOC_HEADER_PATTERNS = [
    re.compile(r"^\s*(table of contents|contents|index)\s*$", re.IGNORECASE),
]


def strip_gutenberg_boilerplate(text: str) -> tuple[str, bool]:
    """
    Remove Gutenberg header and footer.

    Returns:
        Tuple of (cleaned_text, markers_found)
    """
    start_pos = 0
    end_pos = len(text)
    markers_found = False

    # Find start marker
    for pattern in GUTENBERG_START_MARKERS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Skip to end of the line after marker
            line_end = text.find("\n", match.end())
            if line_end != -1:
                start_pos = line_end + 1
                markers_found = True
                logger.info("Found Gutenberg start marker at position %d", match.start())
            break

    # Find end marker
    for pattern in GUTENBERG_END_MARKERS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            end_pos = match.start()
            markers_found = True
            logger.info("Found Gutenberg end marker at position %d", match.start())
            break

    if not markers_found:
        logger.warning("No Gutenberg markers found, keeping full text")

    return text[start_pos:end_pos], markers_found


def detect_and_remove_toc(text: str) -> tuple[str, tuple[int, int] | None]:
    """
    Detect and remove table of contents from text.

    Scans first 15% of text for TOC patterns.

    Returns:
        Tuple of (cleaned_text, toc_range or None)
    """
    scan_limit = int(len(text) * 0.15)
    scan_text = text[:scan_limit]

    toc_start = None
    for pattern in TOC_HEADER_PATTERNS:
        match = pattern.search(scan_text)
        if match:
            toc_start = match.start()
            logger.info("Found TOC header at position %d", toc_start)
            break

    if toc_start is None:
        return text, None

    # Find end of TOC - look for chapter or prose start
    toc_end = _find_toc_end(text, toc_start, scan_limit)

    if toc_end is None:
        logger.info("Could not determine TOC end, not removing")
        return text, None

    logger.info("Removing TOC from %d to %d", toc_start, toc_end)
    cleaned = text[:toc_start] + text[toc_end:]
    return cleaned, (toc_start, toc_end)


def _find_toc_end(text: str, toc_start: int, scan_limit: int) -> int | None:
    """Find the end position of a TOC section."""
    # Look for common patterns that indicate start of actual content
    content_patterns = [
        re.compile(r"^\s*(chapter|part|book)\s+[ivxlcdm\d]+", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*(prologue|introduction|preface)\s*$", re.IGNORECASE | re.MULTILINE),
    ]

    search_text = text[toc_start:scan_limit]
    min_end = None

    for pattern in content_patterns:
        match = pattern.search(search_text)
        if match:
            end_pos = toc_start + match.start()
            if min_end is None or end_pos < min_end:
                min_end = end_pos

    return min_end


def fix_space_before_punctuation(text: str) -> str:
    """
    Remove errant spaces before punctuation.

    Fixes patterns like "a draught , and" -> "a draught, and"
    """
    return re.sub(r"\s+([,\.;:!?])", r"\1", text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    - Convert CRLF to LF
    - Strip trailing whitespace from lines
    - Collapse 3+ consecutive newlines to 2
    """
    # CRLF -> LF
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Strip trailing whitespace from each line
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    text = "\n".join(lines)

    # Collapse 3+ consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def fix_hyphenation(text: str) -> str:
    """
    Fix line-break hyphenation.

    If line ends with '-' and next line starts lowercase, join without hyphen.
    """
    lines = text.split("\n")
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if (
            line.endswith("-")
            and i + 1 < len(lines)
            and lines[i + 1]
            and lines[i + 1][0].islower()
        ):
            # Join with next line, removing hyphen
            next_line = lines[i + 1]
            joined = line[:-1] + next_line
            result.append(joined)
            i += 2
        else:
            result.append(line)
            i += 1

    return "\n".join(result)


def remove_page_artifacts(text: str) -> str:
    """
    Remove standalone page number lines.

    Removes lines that are only standalone Arabic page numbers (1-4 digits).

    Note: Roman numeral lines are NOT stripped here because they are
    commonly used as chapter headings (I, II, III...) and must survive
    until the chapterize stage can detect them.
    """
    lines = text.split("\n")
    cleaned: list[str] = []

    for line in lines:
        if PAGE_NUMBER_PATTERN.match(line):
            continue
        cleaned.append(line)

    return "\n".join(cleaned)


def strip_title_byline(text: str, title: str | None, author: str | None) -> str:
    """
    Strip title and author byline from start of text.

    These are already captured in book.json metadata, so remove from prose.

    Args:
        text: Full text
        title: Book title (from metadata)
        author: Author name (from metadata)

    Returns:
        Text with title/byline removed from start
    """
    if not title and not author:
        return text

    # Look at first ~500 chars for title/byline
    scan_limit = min(500, len(text))
    scan_text = text[:scan_limit]
    lines = scan_text.split("\n")

    lines_to_remove = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line matches or contains title
        if title and _line_matches_title(stripped, title):
            lines_to_remove = i + 1
            logger.debug("Found title line at %d: %s", i, stripped[:50])
            continue

        # Check if line matches author byline pattern
        if author and _line_matches_author(stripped, author):
            lines_to_remove = i + 1
            logger.debug("Found author line at %d: %s", i, stripped[:50])
            continue

        # Stop at first line that's neither title nor author
        if lines_to_remove > 0:
            break

    if lines_to_remove > 0:
        # Find the character position after the lines to remove
        remaining_lines = lines[lines_to_remove:]
        text = "\n".join(remaining_lines) + text[scan_limit:]
        logger.info("Stripped %d title/byline lines from start", lines_to_remove)

    return text


def _line_matches_title(line: str, title: str) -> bool:
    """Check if line is the book title."""
    line_lower = line.lower()
    title_lower = title.lower()

    # Exact match
    if line_lower == title_lower:
        return True

    # Title at start of line
    if line_lower.startswith(title_lower):
        return True

    # Line is subset of title
    if len(line) > 5 and line_lower in title_lower:
        return True

    return False


def _line_matches_author(line: str, author: str) -> bool:
    """Check if line is an author byline."""
    line_lower = line.lower()
    author_lower = author.lower()

    # "By Author Name" pattern
    if line_lower.startswith("by ") and author_lower in line_lower:
        return True

    # Standalone "by" line (author name will be on next line)
    if line_lower == "by":
        return True

    # Just the author name
    if line_lower == author_lower:
        return True

    # Author name at start (sometimes has "Author Name\n")
    if line_lower.startswith(author_lower):
        return True

    return False


def fix_drop_caps(text: str) -> str:
    """
    Rejoin separated drop cap letters.

    Fixes cases where a decorative drop cap letter is on its own line
    followed by the rest of the word on the next line.
    E.g., "M\\n\\nr. Bennet" -> "Mr. Bennet"
    E.g., "M\\nR. BENNET" -> "MR. BENNET"
    E.g., "D\\nURING dinner" -> "DURING dinner"
    E.g., "I\\nT is a truth" -> "IT is a truth"

    Two patterns:
    1. Single uppercase + lowercase continuation (any newline count)
    2. Single uppercase + uppercase word fragment (single newline only).
       A word fragment is detected by the third char being uppercase,
       a period, or whitespace (e.g., R., URING, T is) rather than
       lowercase (e.g., In, The, Elizabeth = normal sentence start).
    """
    # Pattern 1: uppercase + lowercase continuation
    text = re.sub(r"^([A-Z])\n{1,2}([a-z])", r"\1\2", text, flags=re.MULTILINE)
    # Pattern 2: uppercase + uppercase word fragment (single newline for safety)
    text = re.sub(r"^([A-Z])\n([A-Z])(?=[A-Z.\s])", r"\1\2", text, flags=re.MULTILINE)
    return text


def normalize_text(text: str) -> str:
    """Apply all normalization steps to text."""
    text = normalize_whitespace(text)
    text = fix_hyphenation(text)
    text = fix_drop_caps(text)
    text = remove_page_artifacts(text)
    text = fix_space_before_punctuation(text)
    # Final whitespace cleanup after all processing
    text = normalize_whitespace(text)
    return text.strip()
