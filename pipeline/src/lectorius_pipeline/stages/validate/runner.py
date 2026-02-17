"""Validate stage runner."""

import logging
from pathlib import Path

from lectorius_pipeline.config import PipelineConfig
from lectorius_pipeline.errors import ValidationFailedError
from lectorius_pipeline.schemas import Chunk, ValidateReport
from lectorius_pipeline.utils.io import load_chunks, update_manifest

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
    chunks = load_chunks(output_dir)
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
    if success:
        update_manifest(output_dir, "validate")

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



def _write_report(reports_dir: Path, report: ValidateReport) -> None:
    """Write validation.json report."""
    path = reports_dir / "validation.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Wrote %s", path)
