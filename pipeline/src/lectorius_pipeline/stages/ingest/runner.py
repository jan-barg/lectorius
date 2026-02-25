"""Ingest stage runner."""

import json
import logging
import re
from pathlib import Path

from lectorius_pipeline.config import PipelineConfig
from lectorius_pipeline.errors import NoTextExtractedError, SuspiciouslyShortError
from lectorius_pipeline.schemas import BookMeta, IngestReport, LLMAnalysis, Manifest

from .normalizer import (
    detect_and_remove_toc,
    normalize_text,
    strip_gutenberg_boilerplate,
    strip_title_byline,
)
from .parser import parse_epub

logger = logging.getLogger(__name__)


def run_ingest(
    input_path: Path,
    output_dir: Path,
    book_id: str,
    config: PipelineConfig,
    tts_provider: str | None = None,
    voice_id: str | None = None,
) -> IngestReport:
    """
    Run the ingest stage.

    Parses epub, extracts and normalizes text, strips boilerplate.

    Args:
        input_path: Path to epub file
        output_dir: Directory for output files
        book_id: Identifier for the book
        config: Pipeline configuration
        tts_provider: TTS provider to write into book.json ('openai' or 'elevenlabs').
        voice_id: Voice ID to write into book.json.

    Returns:
        IngestReport with processing results

    Raises:
        EpubParseError: If epub cannot be parsed
        NoTextExtractedError: If no text is extracted
        SuspiciouslyShortError: If text is < 1000 chars
    """
    logger.info("Starting ingest stage for %s", book_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    warnings: list[str] = []

    # Parse epub
    raw_text, book_meta = parse_epub(input_path, book_id)
    chars_extracted = len(raw_text)
    logger.info("Extracted %d characters from epub", chars_extracted)

    if not raw_text.strip():
        raise NoTextExtractedError("No text content extracted from epub")

    # Strip Gutenberg boilerplate
    text, gutenberg_found = strip_gutenberg_boilerplate(raw_text)
    if not gutenberg_found:
        warnings.append("No Gutenberg markers found")

    # Detect and remove TOC
    text, toc_range = detect_and_remove_toc(text)
    toc_detected = toc_range is not None
    if toc_detected:
        logger.info("Removed TOC (%d chars)", toc_range[1] - toc_range[0])

    # Normalize text
    text = normalize_text(text)

    # Strip title/byline from start (already in metadata)
    text = strip_title_byline(text, book_meta.title, book_meta.author)

    # Optional LLM-assisted analysis
    llm_analysis: LLMAnalysis | None = None
    llm_assist_used = config.llm_assist

    if config.llm_assist:
        try:
            from .llm_assist import run_llm_analysis

            llm_analysis = run_llm_analysis(
                text, book_meta.title, book_meta.author, config.llm_model
            )
            logger.info("LLM analysis completed successfully")

            text = _apply_narrative_boundaries(text, llm_analysis, warnings)
            text = _apply_junk_patterns(text, llm_analysis, warnings)
            text, caption_count = _strip_duplicate_captions(text)
            if caption_count:
                logger.info("Stripped %d duplicate illustration captions", caption_count)
                warnings.append(f"Stripped {caption_count} duplicate illustration captions")

        except Exception as e:
            logger.warning("LLM analysis failed, continuing without: %s", e)
            warnings.append(f"LLM analysis failed: {e}")
            llm_analysis = None

    chars_after_cleanup = len(text)
    logger.info("Text after cleanup: %d characters", chars_after_cleanup)

    # Validate minimum length
    if chars_after_cleanup < config.min_text_length:
        raise SuspiciouslyShortError(
            f"Text is suspiciously short ({chars_after_cleanup} chars < {config.min_text_length})"
        )

    # Set TTS fields if provided
    if tts_provider:
        book_meta.tts_provider = tts_provider  # type: ignore[assignment]
    if voice_id:
        book_meta.voice_id = voice_id

    # Write outputs
    _write_raw_text(output_dir, text)
    _write_book_meta(output_dir, book_meta)
    _write_manifest(output_dir, book_id, chars_after_cleanup, config)

    report = IngestReport(
        success=True,
        book_id=book_id,
        source_path=str(input_path),
        chars_extracted=chars_extracted,
        chars_after_cleanup=chars_after_cleanup,
        gutenberg_markers_found=gutenberg_found,
        toc_detected=toc_detected,
        toc_char_range=toc_range,
        llm_analysis=llm_analysis,
        llm_assist_used=llm_assist_used,
        warnings=warnings,
    )

    _write_report(reports_dir, report)
    logger.info("Ingest stage completed successfully")
    return report


def _write_raw_text(output_dir: Path, text: str) -> None:
    """Write raw_text.txt."""
    path = output_dir / "raw_text.txt"
    path.write_text(text, encoding="utf-8")
    logger.debug("Wrote %s", path)


def _write_book_meta(output_dir: Path, meta: BookMeta) -> None:
    """Write book.json."""
    path = output_dir / "book.json"
    path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Wrote %s", path)


def _write_manifest(
    output_dir: Path,
    book_id: str,
    total_chars: int,
    config: PipelineConfig,
) -> None:
    """Write or update manifest.json."""
    path = output_dir / "manifest.json"

    manifest = Manifest(
        book_id=book_id,
        pipeline_version=config.pipeline_version,
        stages_completed=["ingest"],
    )
    manifest.stats.total_chars = total_chars
    manifest.config.chunk_target_chars = config.chunking.target_chars
    manifest.config.chunk_min_chars = config.chunking.min_chars
    manifest.config.chunk_max_chars = config.chunking.max_chars

    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Wrote %s", path)


def _write_report(reports_dir: Path, report: IngestReport) -> None:
    """Write ingest.json report."""
    path = reports_dir / "ingest.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Wrote %s", path)


def _find_phrase_fuzzy(text: str, phrase: str) -> int:
    """Find phrase in text, allowing whitespace and case differences."""
    words = phrase.split()[:5]
    if len(words) < 3:
        idx = text.find(phrase)
        if idx >= 0:
            return idx
        # Fall back to case-insensitive
        lower_text = text.lower()
        return lower_text.find(phrase.lower())
    pattern = r"\s+".join(re.escape(w) for w in words)
    match = re.search(pattern, text)
    if not match:
        match = re.search(pattern, text, re.IGNORECASE)
    return match.start() if match else -1


def _include_preceding_headings(text: str, idx: int) -> int:
    """Walk backwards from trim point to include short heading paragraphs.

    LLM start markers often point to the first prose line, missing the
    chapter heading that precedes it (e.g. 'STAVE ONE / MARLEY'S GHOST').
    Scans back over blank-line-delimited blocks that look like headings.
    """
    pos = idx
    for _ in range(4):  # At most 4 paragraphs back
        # Find previous paragraph boundary
        prev_break = text.rfind("\n\n", 0, pos)
        if prev_break < 0:
            # Reached start of text — include everything
            return 0
        block = text[prev_break + 2 : pos].strip()
        if not block:
            pos = prev_break
            continue
        # Include if short and heading-like (all lines < 60 chars, total < 200 chars)
        lines = block.split("\n")
        if len(block) < 200 and all(len(line.strip()) < 60 for line in lines):
            pos = prev_break + 2
        else:
            break
    return pos


def _strip_duplicate_captions(text: str) -> tuple[str, int]:
    """Remove duplicated ALL-CAPS lines (illustration caption artifacts).

    EPUBs with illustrations often extract both the caption and the alt-text,
    producing the same ALL-CAPS line twice in a row separated by a blank line.
    This safely strips both copies since real chapter headings are never
    duplicated.
    """
    count = 0
    paragraphs = re.split(r"\n{2,}", text)
    cleaned: list[str] = []
    skip_next = False

    for i, para in enumerate(paragraphs):
        if skip_next:
            skip_next = False
            continue
        stripped = para.strip()
        if not stripped:
            cleaned.append(para)
            continue
        # Check if this paragraph and the next are duplicates and ALL-CAPS
        if i + 1 < len(paragraphs):
            next_stripped = paragraphs[i + 1].strip()
            # Exact duplicate or one wraps differently (normalize whitespace)
            this_norm = " ".join(stripped.split())
            next_norm = " ".join(next_stripped.split())
            if (
                this_norm == next_norm
                and this_norm == this_norm.upper()
                and len(this_norm) >= 8
                and any(c.isalpha() for c in this_norm)
            ):
                logger.debug("Stripped duplicate caption: '%s'", this_norm[:80])
                count += 1
                skip_next = True
                continue
        cleaned.append(para)

    return "\n\n".join(cleaned), count


def _apply_narrative_boundaries(
    text: str, analysis: LLMAnalysis, warnings: list[str]
) -> str:
    """Trim text to narrative boundaries identified by LLM."""
    max_trim_ratio = 0.50  # Never trim more than 50% from either end

    if analysis.narrative_start_marker:
        idx = _find_phrase_fuzzy(text, analysis.narrative_start_marker)
        if idx > 0:
            if idx < len(text) * max_trim_ratio:
                # Walk back over short heading-like paragraphs so we keep
                # the chapter heading that precedes the first prose line
                # (e.g. "STAVE ONE\n\nMARLEY'S GHOST" before "Marley was dead...")
                idx = _include_preceding_headings(text, idx)
                logger.info("Trimmed %d chars of front matter", idx)
                warnings.append(f"LLM trimmed {idx} chars of front matter")
                text = text[idx:]
            else:
                pct = (idx * 100) // len(text)
                logger.warning("Start marker at %d%% of text, skipping trim", pct)
                warnings.append(f"LLM start marker too deep ({pct}%), skipped")
        elif idx < 0:
            logger.warning("Could not find narrative start marker in text")
            warnings.append("LLM start marker not found in text")

    if analysis.narrative_end_marker:
        idx = _find_phrase_fuzzy(text, analysis.narrative_end_marker)
        if idx > 0:
            end_pos = idx + len(analysis.narrative_end_marker)
            # Include to end of paragraph
            next_break = text.find("\n\n", end_pos)
            if next_break > 0:
                end_pos = next_break
            if end_pos > len(text) * max_trim_ratio:
                trimmed = len(text) - end_pos
                logger.info("Trimmed %d chars of back matter", trimmed)
                warnings.append(f"LLM trimmed {trimmed} chars of back matter")
                text = text[:end_pos]
            else:
                pct = (end_pos * 100) // len(text)
                logger.warning("End marker at %d%% of text, skipping trim", pct)
                warnings.append(f"LLM end marker too early ({pct}%), skipped")
        elif idx < 0:
            logger.warning("Could not find narrative end marker in text")
            warnings.append("LLM end marker not found in text")

    return text


def _apply_junk_patterns(
    text: str, analysis: LLMAnalysis, warnings: list[str]
) -> str:
    """Strip junk patterns identified by LLM from text."""
    for i, pattern_str in enumerate(analysis.junk_patterns):
        try:
            pattern = re.compile(pattern_str, re.MULTILINE)
            matches = pattern.findall(text)
            if matches:
                text = pattern.sub("", text)
                desc = (
                    analysis.junk_patterns[i]
                    if i < len(analysis.junk_patterns)
                    else pattern_str
                )
                logger.info("Stripped %d occurrences of: %s", len(matches), desc)
                warnings.append(
                    f"LLM stripped {len(matches)} occurrences of: {desc}"
                )
        except re.error as e:
            logger.warning("Invalid junk pattern '%s': %s", pattern_str, e)
            warnings.append(f"Invalid LLM junk pattern skipped: {pattern_str}")

    return text
