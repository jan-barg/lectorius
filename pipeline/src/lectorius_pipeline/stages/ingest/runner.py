"""Ingest stage runner."""

import json
import logging
from pathlib import Path

from lectorius_pipeline.config import PipelineConfig
from lectorius_pipeline.errors import NoTextExtractedError, SuspiciouslyShortError
from lectorius_pipeline.schemas import BookMeta, IngestReport, Manifest

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
) -> IngestReport:
    """
    Run the ingest stage.

    Parses epub, extracts and normalizes text, strips boilerplate.

    Args:
        input_path: Path to epub file
        output_dir: Directory for output files
        book_id: Identifier for the book
        config: Pipeline configuration

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

    chars_after_cleanup = len(text)
    logger.info("Text after cleanup: %d characters", chars_after_cleanup)

    # Validate minimum length
    if chars_after_cleanup < config.min_text_length:
        raise SuspiciouslyShortError(
            f"Text is suspiciously short ({chars_after_cleanup} chars < {config.min_text_length})"
        )

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
