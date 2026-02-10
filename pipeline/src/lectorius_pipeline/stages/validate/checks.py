"""Validation checks for chunks."""

import logging
import re
from collections import Counter

from lectorius_pipeline.config import ChunkConfig
from lectorius_pipeline.schemas import Chunk, ValidationIssue

logger = logging.getLogger(__name__)


def check_empty_text(chunk: Chunk) -> ValidationIssue | None:
    """Check if chunk text is empty."""
    if not chunk.text.strip():
        return ValidationIssue(
            severity="ERROR",
            check="empty_text",
            message="Chunk has empty text",
            chunk_id=chunk.chunk_id,
            chunk_index=chunk.chunk_index,
        )
    return None


def check_too_short(chunk: Chunk, min_chars: int) -> ValidationIssue | None:
    """Check if chunk is below minimum length."""
    if len(chunk.text) < min_chars:
        return ValidationIssue(
            severity="WARN",
            check="too_short",
            message=f"Chunk is too short ({len(chunk.text)} < {min_chars} chars)",
            chunk_id=chunk.chunk_id,
            chunk_index=chunk.chunk_index,
        )
    return None


def check_too_long(chunk: Chunk, max_chars: int) -> ValidationIssue | None:
    """Check if chunk exceeds maximum length."""
    if len(chunk.text) > max_chars:
        return ValidationIssue(
            severity="ERROR",
            check="too_long",
            message=f"Chunk exceeds max length ({len(chunk.text)} > {max_chars} chars)",
            chunk_id=chunk.chunk_id,
            chunk_index=chunk.chunk_index,
        )
    return None


def check_non_prose(chunk: Chunk) -> ValidationIssue | None:
    """Check if chunk is only digits/punctuation/whitespace."""
    text = chunk.text.strip()
    if not text:
        return None

    # Remove all non-letter characters
    letters_only = re.sub(r"[^a-zA-Z]", "", text)
    if not letters_only:
        return ValidationIssue(
            severity="WARN",
            check="non_prose",
            message="Chunk contains only digits/punctuation/whitespace",
            chunk_id=chunk.chunk_id,
            chunk_index=chunk.chunk_index,
        )
    return None


def check_duplicate_ids(chunks: list[Chunk]) -> list[ValidationIssue]:
    """Check for duplicate chunk_id values."""
    issues: list[ValidationIssue] = []
    id_counts = Counter(c.chunk_id for c in chunks)

    for chunk_id, count in id_counts.items():
        if count > 1:
            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    check="duplicate_chunk_id",
                    message=f"chunk_id '{chunk_id}' appears {count} times",
                    chunk_id=chunk_id,
                )
            )

    return issues


def check_duplicate_text(chunks: list[Chunk]) -> list[ValidationIssue]:
    """Check for duplicate text content."""
    issues: list[ValidationIssue] = []
    text_to_ids: dict[str, list[str]] = {}

    for chunk in chunks:
        text = chunk.text.strip()
        if text not in text_to_ids:
            text_to_ids[text] = []
        text_to_ids[text].append(chunk.chunk_id)

    for text, ids in text_to_ids.items():
        if len(ids) > 1:
            issues.append(
                ValidationIssue(
                    severity="WARN",
                    check="duplicate_text",
                    message=f"Duplicate text in chunks: {', '.join(ids)}",
                )
            )

    return issues


def check_index_sequence(chunks: list[Chunk]) -> list[ValidationIssue]:
    """Check that chunk_index values are sequential without gaps."""
    issues: list[ValidationIssue] = []

    if not chunks:
        return issues

    indices = sorted(c.chunk_index for c in chunks)

    # Check starts at 1
    if indices[0] != 1:
        issues.append(
            ValidationIssue(
                severity="ERROR",
                check="chunk_index_gap",
                message=f"chunk_index should start at 1, found {indices[0]}",
            )
        )

    # Check sequential
    for i in range(1, len(indices)):
        if indices[i] != indices[i - 1] + 1:
            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    check="chunk_index_gap",
                    message=f"Gap in chunk_index: {indices[i-1]} to {indices[i]}",
                )
            )

    return issues


def check_offset_sequence(chunks: list[Chunk]) -> list[ValidationIssue]:
    """Check that chunk offsets don't overlap and don't have large gaps."""
    issues: list[ValidationIssue] = []

    if len(chunks) < 2:
        return issues

    sorted_chunks = sorted(chunks, key=lambda c: c.char_start)

    for i in range(1, len(sorted_chunks)):
        prev = sorted_chunks[i - 1]
        curr = sorted_chunks[i]

        # Check for overlap
        if prev.char_end > curr.char_start:
            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    check="offset_overlap",
                    message=(
                        f"Offset overlap: {prev.chunk_id} ends at {prev.char_end}, "
                        f"{curr.chunk_id} starts at {curr.char_start}"
                    ),
                    chunk_id=curr.chunk_id,
                    chunk_index=curr.chunk_index,
                )
            )

        # Check for gap (warn only if significant)
        gap = curr.char_start - prev.char_end
        if gap > 100:  # More than 100 chars gap
            issues.append(
                ValidationIssue(
                    severity="WARN",
                    check="offset_gap",
                    message=f"Gap of {gap} chars between {prev.chunk_id} and {curr.chunk_id}",
                    chunk_id=curr.chunk_id,
                    chunk_index=curr.chunk_index,
                )
            )

    return issues


def validate_chunks(chunks: list[Chunk], config: ChunkConfig) -> list[ValidationIssue]:
    """Run all validation checks on chunks."""
    issues: list[ValidationIssue] = []

    # Per-chunk checks
    for chunk in chunks:
        issue = check_empty_text(chunk)
        if issue:
            issues.append(issue)

        issue = check_too_short(chunk, config.min_chars)
        if issue:
            issues.append(issue)

        issue = check_too_long(chunk, config.max_chars)
        if issue:
            issues.append(issue)

        issue = check_non_prose(chunk)
        if issue:
            issues.append(issue)

    # Cross-chunk checks
    issues.extend(check_duplicate_ids(chunks))
    issues.extend(check_duplicate_text(chunks))
    issues.extend(check_index_sequence(chunks))
    issues.extend(check_offset_sequence(chunks))

    return issues
