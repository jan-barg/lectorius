"""Chapter boundary detection."""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Chapter detection patterns
CHAPTER_PATTERNS = [
    (
        "chapter_numbered",
        re.compile(r"^\s*(chapter|ch\.?)\s*(\d+|[ivxlcdm]+)\.?\s*(.*)$", re.IGNORECASE),
    ),
    (
        "part_book",
        re.compile(r"^\s*(part|book)\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$", re.IGNORECASE),
    ),
    (
        "section_markers",
        re.compile(r"^\s*(prologue|epilogue|introduction|preface|foreword|afterword|postscript)\s*$", re.IGNORECASE),
    ),
    (
        "polish_chapter",
        re.compile(r"^\s*(rozdzia[łl])\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$", re.IGNORECASE),
    ),
    (
        "roman_numeral_line",
        re.compile(r"^\s*[IVXLCDM]{1,8}\s*$"),
    ),
    (
        "numbered_title",
        re.compile(r"^\s*\d{1,3}\.\s+[A-Z]"),
    ),
    (
        "all_caps_header",
        re.compile(r"^[A-Z][A-Z\s\-\']{5,50}$"),
    ),
]


@dataclass
class ChapterCandidate:
    """Potential chapter boundary."""

    line_number: int
    char_start: int
    title: str
    pattern_name: str


def detect_chapter_boundaries(
    text: str,
    llm_chapter_pattern: str | None = None,
) -> list[ChapterCandidate]:
    """
    Detect potential chapter boundaries in text.

    Scans text line by line and identifies chapter headers.

    Args:
        text: Full text to scan
        llm_chapter_pattern: Optional regex from LLM analysis, prepended to patterns

    Returns:
        List of ChapterCandidate in order of appearance
    """
    # Build patterns list, optionally prepending LLM-detected pattern
    patterns = list(CHAPTER_PATTERNS)
    if llm_chapter_pattern:
        try:
            compiled = re.compile(llm_chapter_pattern, re.IGNORECASE)
            # Reject patterns that match empty strings or trivially short strings
            if compiled.match("") or compiled.match(" "):
                logger.warning("LLM chapter pattern '%s' matches empty/blank lines, skipping", llm_chapter_pattern)
            else:
                patterns.insert(0, ("llm_detected", compiled))
                logger.info("Prepended LLM chapter pattern to detection list")
        except re.error as e:
            logger.warning("Invalid LLM chapter pattern '%s': %s", llm_chapter_pattern, e)

    candidates: list[ChapterCandidate] = []
    lines = text.split("\n")
    char_offset = 0

    for line_num, line in enumerate(lines):
        # Check position - must be at start or after blank line
        if line_num > 0 and lines[line_num - 1].strip():
            char_offset += len(line) + 1
            continue

        # Try each pattern
        for pattern_name, pattern in patterns:
            if pattern.match(line):
                # Reject single-letter roman numeral matches that are drop caps
                if pattern_name == "roman_numeral_line" and _is_drop_cap(lines, line_num):
                    logger.debug(
                        "Skipping drop cap '%s' at line %d", line.strip(), line_num
                    )
                    break

                # Validate with context
                if _validate_chapter_context(lines, line_num):
                    title = _extract_title(line, pattern_name)
                    candidates.append(
                        ChapterCandidate(
                            line_number=line_num,
                            char_start=char_offset,
                            title=title,
                            pattern_name=pattern_name,
                        )
                    )
                    logger.debug(
                        "Found chapter candidate: '%s' at line %d (pattern: %s)",
                        title,
                        line_num,
                        pattern_name,
                    )
                break

        char_offset += len(line) + 1

    return candidates


def _is_drop_cap(lines: list[str], line_num: int) -> bool:
    """Check if a single-letter line is a drop cap rather than a chapter heading.

    Detects both lowercase continuations (M + r. Bennet) and uppercase
    word fragments (M + R. BENNET, D + URING).  A word fragment starts
    with uppercase followed by uppercase, period, or whitespace, while
    a normal sentence start has uppercase followed by lowercase.
    """
    line = lines[line_num].strip()
    if len(line) != 1:
        return False
    # Check next non-blank line
    for i in range(line_num + 1, min(line_num + 4, len(lines))):
        stripped = lines[i].strip()
        if stripped:
            # Lowercase start = clearly a drop cap (e.g., "r. Bennet")
            if stripped[0].islower():
                return True
            # Uppercase word fragment: second char is uppercase, period,
            # or whitespace (R., URING, T is) — not a normal sentence
            # start like "Elizabeth" or "The" (uppercase + lowercase)
            if len(stripped) >= 2 and (stripped[1].isupper() or stripped[1] in ".  "):
                return True
            return False
    return False


def _validate_chapter_context(lines: list[str], line_num: int) -> bool:
    """
    Validate chapter candidate by examining following context.

    Returns True if the following 6 lines look like prose.
    """
    # Check lines after the candidate
    context_lines = lines[line_num + 1 : line_num + 7]
    if not context_lines:
        return True  # End of file is OK

    # Count prose-like lines (non-empty, not all caps, has lowercase)
    prose_count = 0
    for line in context_lines:
        stripped = line.strip()
        if stripped and not stripped.isupper() and any(c.islower() for c in stripped):
            prose_count += 1

    # Require at least 2 prose-like lines in context
    return prose_count >= 2


def _extract_title(line: str, pattern_name: str) -> str:
    """Extract clean title from chapter header line."""
    line = line.strip()

    if pattern_name in ("chapter_numbered", "part_book", "polish_chapter"):
        # Try to extract title after number
        match = re.match(
            r"^(chapter|ch\.?|part|book|rozdzia[łl])\s*(\d+|[ivxlcdm]+)\.?\s*(.*)$",
            line,
            re.IGNORECASE,
        )
        if match:
            prefix = match.group(1)
            number = match.group(2)
            suffix = match.group(3).strip()
            if suffix:
                return f"{prefix.title()} {number.upper()}: {suffix}"
            return f"{prefix.title()} {number.upper()}"

    if pattern_name == "section_markers":
        return line.title()

    if pattern_name == "roman_numeral_line":
        return line.strip().upper()

    if pattern_name == "numbered_title":
        return line.strip()

    if pattern_name == "all_caps_header":
        return line.strip().title()

    if pattern_name == "llm_detected":
        return line.strip()

    return line.strip()
