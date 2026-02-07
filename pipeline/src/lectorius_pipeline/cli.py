"""CLI interface for lectorius pipeline."""

import logging
import sys
from pathlib import Path
from typing import Literal

import click

from lectorius_pipeline.config import DEFAULT_CONFIG, PipelineConfig
from lectorius_pipeline.errors import PipelineError
from lectorius_pipeline.stages.chapterize import run_chapterize
from lectorius_pipeline.stages.chunkify import run_chunkify
from lectorius_pipeline.stages.ingest import run_ingest
from lectorius_pipeline.stages.validate import run_validate

# Stage order
STAGES = ["ingest", "chapterize", "chunkify", "validate"]

StageType = Literal["ingest", "chapterize", "chunkify", "validate"]


def setup_logging(verbose: bool) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.version_option(version="1.0.0")
def main() -> None:
    """Lectorius pipeline - transform epubs into book packs."""
    pass


@main.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to epub file",
)
@click.option(
    "--book-id",
    required=True,
    help="Book identifier (lowercase alphanumeric with hyphens)",
)
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(path_type=Path),
    help="Output directory for book pack",
)
@click.option(
    "--stop-after",
    type=click.Choice(STAGES),
    default=None,
    help="Stop after this stage",
)
@click.option(
    "--from-stage",
    type=click.Choice(STAGES),
    default=None,
    help="Start from this stage (requires existing outputs)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def process(
    input_path: Path,
    book_id: str,
    output_dir: Path,
    stop_after: str | None,
    from_stage: str | None,
    verbose: bool,
) -> None:
    """
    Process an epub through the pipeline.

    Runs all stages from ingest through validate (or specified subset).
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    config = DEFAULT_CONFIG

    # Determine which stages to run
    start_idx = STAGES.index(from_stage) if from_stage else 0
    end_idx = STAGES.index(stop_after) + 1 if stop_after else len(STAGES)
    stages_to_run = STAGES[start_idx:end_idx]

    logger.info("Processing %s through stages: %s", book_id, ", ".join(stages_to_run))

    try:
        for stage in stages_to_run:
            if stage == "ingest":
                run_ingest(input_path, output_dir, book_id, config)
            elif stage == "chapterize":
                run_chapterize(output_dir, book_id)
            elif stage == "chunkify":
                run_chunkify(output_dir, book_id, config)
            elif stage == "validate":
                run_validate(output_dir, book_id, config)

        logger.info("Pipeline completed successfully")
        click.echo(f"Book pack created at: {output_dir}")

    except PipelineError as e:
        logger.error("Pipeline failed at stage '%s': %s", e.stage, str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)


@main.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to epub file",
)
@click.option(
    "--book-id",
    required=True,
    help="Book identifier",
)
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(path_type=Path),
    help="Output directory",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def ingest(
    input_path: Path,
    book_id: str,
    output_dir: Path,
    verbose: bool,
) -> None:
    """Run the ingest stage only."""
    setup_logging(verbose)
    config = DEFAULT_CONFIG

    try:
        report = run_ingest(input_path, output_dir, book_id, config)
        click.echo(f"Ingest completed: {report.chars_after_cleanup} chars extracted")
    except PipelineError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--book-dir",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Book output directory",
)
@click.option(
    "--book-id",
    required=True,
    help="Book identifier",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def chapterize(book_dir: Path, book_id: str, verbose: bool) -> None:
    """Run the chapterize stage only."""
    setup_logging(verbose)

    try:
        report = run_chapterize(book_dir, book_id)
        click.echo(f"Chapterize completed: {report.chapters_detected} chapters")
    except PipelineError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--book-dir",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Book output directory",
)
@click.option(
    "--book-id",
    required=True,
    help="Book identifier",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def chunkify(book_dir: Path, book_id: str, verbose: bool) -> None:
    """Run the chunkify stage only."""
    setup_logging(verbose)
    config = DEFAULT_CONFIG

    try:
        report = run_chunkify(book_dir, book_id, config)
        click.echo(f"Chunkify completed: {report.total_chunks} chunks")
    except PipelineError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--book-dir",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Book output directory",
)
@click.option(
    "--book-id",
    required=True,
    help="Book identifier",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def validate(book_dir: Path, book_id: str, verbose: bool) -> None:
    """Run the validate stage only."""
    setup_logging(verbose)
    config = DEFAULT_CONFIG

    try:
        report = run_validate(book_dir, book_id, config)
        click.echo(
            f"Validation passed: {report.total_chunks} chunks, "
            f"{report.warning_count} warnings"
        )
    except PipelineError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
