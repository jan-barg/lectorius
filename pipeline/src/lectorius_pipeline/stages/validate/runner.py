"""Validate stage runner."""

import logging
from pathlib import Path

from lectorius_pipeline.config import PipelineConfig
from lectorius_pipeline.errors import ValidationFailedError
from lectorius_pipeline.schemas import Chunk, Manifest, ValidateReport

from .checks import validate_chunks

logger = logging.getLogger(__name__)


def run_validate(output_dir: Path, book_id: str, config: PipelineConfig) -> ValidateReport:
    """
    Run the validate stage.

    Validates all chunks for errors and warnings.

    Args:
        output_dir: Book output directory
        book_id: Book identifier
        config: Pipeline configuration

    Returns:
        ValidateReport with validation results

    Raises:
        ValidationFailedError: If any ERROR-level issues are found
    """
    logger.info("Starting validate stage for %s", book_id)

    # Load chunks
    chunks = _load_chunks(output_dir)
    logger.info("Loaded %d chunks for validation", len(chunks))

    # Run validation
    issues = validate_chunks(chunks, config.chunking)

    # Count by severity
    error_count = sum(1 for i in issues if i.severity == "ERROR")
    warning_count = sum(1 for i in issues if i.severity == "WARN")

    logger.info("Validation found %d errors, %d warnings", error_count, warning_count)

    # Log issues
    for issue in issues:
        if issue.severity == "ERROR":
            logger.error("[%s] %s", issue.check, issue.message)
        else:
            logger.warning("[%s] %s", issue.check, issue.message)

    success = error_count == 0

    # Update manifest
    _update_manifest(output_dir, success)

    report = ValidateReport(
        success=success,
        book_id=book_id,
        total_chunks=len(chunks),
        issues=issues,
        error_count=error_count,
        warning_count=warning_count,
    )
    _write_report(output_dir / "reports", report)

    if not success:
        raise ValidationFailedError(error_count)

    logger.info("Validate stage completed successfully")
    return report


def _load_chunks(output_dir: Path) -> list[Chunk]:
    """Load chunks from chunks.jsonl."""
    path = output_dir / "chunks.jsonl"
    chunks: list[Chunk] = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        if line:
            chunks.append(Chunk.model_validate_json(line))
    return chunks


def _update_manifest(output_dir: Path, success: bool) -> None:
    """Update manifest.json with validate stage."""
    path = output_dir / "manifest.json"
    manifest = Manifest.model_validate_json(path.read_text())

    if success and "validate" not in manifest.stages_completed:
        manifest.stages_completed.append("validate")

    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Updated %s", path)


def _write_report(reports_dir: Path, report: ValidateReport) -> None:
    """Write validation.json report."""
    path = reports_dir / "validation.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Wrote %s", path)
