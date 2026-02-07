"""Chapterize stage runner."""

import json
import logging
from collections import Counter
from pathlib import Path

from lectorius_pipeline.errors import OverlappingChaptersError
from lectorius_pipeline.schemas import Chapter, ChapterizeReport, Manifest

from .detector import ChapterCandidate, detect_chapter_boundaries

logger = logging.getLogger(__name__)

MIN_CHAPTER_CHARS = 500
LARGE_CHAPTER_THRESHOLD = 0.20  # 20% of book


def run_chapterize(output_dir: Path, book_id: str) -> ChapterizeReport:
    """
    Run the chapterize stage.

    Detects chapter boundaries from raw_text.txt.

    Args:
        output_dir: Book output directory
        book_id: Book identifier

    Returns:
        ChapterizeReport with processing results
    """
    logger.info("Starting chapterize stage for %s", book_id)

    raw_text_path = output_dir / "raw_text.txt"
    text = raw_text_path.read_text(encoding="utf-8")
    text_length = len(text)

    warnings: list[str] = []
    fallback_used = False

    # Detect candidates
    candidates = detect_chapter_boundaries(text)
    logger.info("Found %d chapter candidates", len(candidates))

    # Count pattern matches
    pattern_counts = Counter(c.pattern_name for c in candidates)

    # Build chapters from candidates
    if candidates:
        chapters = _build_chapters_from_candidates(candidates, text_length, book_id)
    else:
        logger.warning("No chapters detected, creating single chapter")
        chapters = [_create_fallback_chapter(book_id, text_length)]
        fallback_used = True
        warnings.append("No chapter boundaries detected, created single 'Full Text' chapter")

    # Merge tiny chapters
    chapters, merge_warnings = _merge_tiny_chapters(chapters, text, book_id)
    warnings.extend(merge_warnings)

    # Validate no overlaps
    _validate_no_overlaps(chapters)

    # Check for large chapters
    for chapter in chapters:
        chapter_chars = chapter.char_end - chapter.char_start
        if chapter_chars > text_length * LARGE_CHAPTER_THRESHOLD:
            pct = (chapter_chars / text_length) * 100
            warnings.append(f"Chapter '{chapter.title}' is {pct:.1f}% of book")

    # Write outputs
    _write_chapters(output_dir, chapters)
    _update_manifest(output_dir, len(chapters))

    report = ChapterizeReport(
        success=True,
        book_id=book_id,
        chapters_detected=len(chapters),
        pattern_matches=dict(pattern_counts),
        fallback_used=fallback_used,
        warnings=warnings,
    )
    _write_report(output_dir / "reports", report)

    logger.info("Chapterize stage completed: %d chapters", len(chapters))
    return report


def _build_chapters_from_candidates(
    candidates: list[ChapterCandidate],
    text_length: int,
    book_id: str,
) -> list[Chapter]:
    """Build Chapter objects from candidates."""
    chapters: list[Chapter] = []

    for i, candidate in enumerate(candidates):
        index = i + 1
        chapter_id = f"{book_id}_ch{index:03d}"

        # Determine char_end
        if i + 1 < len(candidates):
            char_end = candidates[i + 1].char_start
        else:
            char_end = text_length

        chapters.append(
            Chapter(
                book_id=book_id,
                chapter_id=chapter_id,
                index=index,
                title=candidate.title,
                char_start=candidate.char_start,
                char_end=char_end,
            )
        )

    return chapters


def _create_fallback_chapter(book_id: str, text_length: int) -> Chapter:
    """Create a single fallback chapter for the entire book."""
    return Chapter(
        book_id=book_id,
        chapter_id=f"{book_id}_ch001",
        index=1,
        title="Full Text",
        char_start=0,
        char_end=text_length,
    )


def _merge_tiny_chapters(
    chapters: list[Chapter],
    text: str,
    book_id: str,
) -> tuple[list[Chapter], list[str]]:
    """Merge chapters smaller than MIN_CHAPTER_CHARS with previous."""
    if len(chapters) <= 1:
        return chapters, []

    warnings: list[str] = []
    merged: list[Chapter] = []

    for chapter in chapters:
        chapter_chars = chapter.char_end - chapter.char_start

        if chapter_chars < MIN_CHAPTER_CHARS and merged:
            # Merge with previous chapter
            prev = merged[-1]
            warnings.append(
                f"Merged tiny chapter '{chapter.title}' ({chapter_chars} chars) "
                f"with '{prev.title}'"
            )
            merged[-1] = Chapter(
                book_id=book_id,
                chapter_id=prev.chapter_id,
                index=prev.index,
                title=prev.title,
                char_start=prev.char_start,
                char_end=chapter.char_end,
            )
        else:
            merged.append(chapter)

    # Renumber chapters
    result: list[Chapter] = []
    for i, chapter in enumerate(merged):
        index = i + 1
        result.append(
            Chapter(
                book_id=book_id,
                chapter_id=f"{book_id}_ch{index:03d}",
                index=index,
                title=chapter.title,
                char_start=chapter.char_start,
                char_end=chapter.char_end,
            )
        )

    return result, warnings


def _validate_no_overlaps(chapters: list[Chapter]) -> None:
    """Validate that chapter ranges do not overlap."""
    for i in range(len(chapters) - 1):
        current = chapters[i]
        next_ch = chapters[i + 1]
        if current.char_end > next_ch.char_start:
            raise OverlappingChaptersError(
                f"Chapter {current.chapter_id} end ({current.char_end}) "
                f"overlaps with {next_ch.chapter_id} start ({next_ch.char_start})"
            )


def _write_chapters(output_dir: Path, chapters: list[Chapter]) -> None:
    """Write chapters.jsonl."""
    path = output_dir / "chapters.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for chapter in chapters:
            f.write(chapter.model_dump_json() + "\n")
    logger.debug("Wrote %s", path)


def _update_manifest(output_dir: Path, chapter_count: int) -> None:
    """Update manifest.json with chapterize stage."""
    path = output_dir / "manifest.json"
    manifest = Manifest.model_validate_json(path.read_text())

    if "chapterize" not in manifest.stages_completed:
        manifest.stages_completed.append("chapterize")
    manifest.stats.chapters = chapter_count

    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Updated %s", path)


def _write_report(reports_dir: Path, report: ChapterizeReport) -> None:
    """Write chapters.json report."""
    path = reports_dir / "chapters.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Wrote %s", path)
