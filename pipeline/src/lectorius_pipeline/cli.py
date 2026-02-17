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
from lectorius_pipeline.stages.memory import run_memory
from lectorius_pipeline.stages.rag import run_rag
from lectorius_pipeline.stages.tts import run_tts
from lectorius_pipeline.stages.validate import run_validate

# Core text-processing stages (used by the `process` command).
# TTS, RAG, and Memory are separate commands — see below.
TEXT_STAGES = ["ingest", "chapterize", "chunkify", "validate"]

TextStageType = Literal["ingest", "chapterize", "chunkify", "validate"]


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
    type=click.Choice(TEXT_STAGES),
    default=None,
    help="Stop after this stage",
)
@click.option(
    "--from-stage",
    type=click.Choice(TEXT_STAGES),
    default=None,
    help="Start from this stage (requires existing outputs)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--llm-assist",
    is_flag=True,
    default=False,
    help="Use Claude to analyze text structure at ingest",
)
def process(
    input_path: Path,
    book_id: str,
    output_dir: Path,
    stop_after: str | None,
    from_stage: str | None,
    verbose: bool,
    llm_assist: bool,
) -> None:
    """
    Process an epub through the pipeline.

    Runs all stages from ingest through validate (or specified subset).
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    config = PipelineConfig(llm_assist=llm_assist) if llm_assist else DEFAULT_CONFIG

    # Determine which stages to run
    start_idx = TEXT_STAGES.index(from_stage) if from_stage else 0
    end_idx = TEXT_STAGES.index(stop_after) + 1 if stop_after else len(TEXT_STAGES)
    stages_to_run = TEXT_STAGES[start_idx:end_idx]

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
@click.option(
    "--llm-assist",
    is_flag=True,
    default=False,
    help="Use Claude to analyze text structure",
)
def ingest(
    input_path: Path,
    book_id: str,
    output_dir: Path,
    verbose: bool,
    llm_assist: bool,
) -> None:
    """Run the ingest stage only."""
    setup_logging(verbose)
    config = PipelineConfig(llm_assist=llm_assist) if llm_assist else DEFAULT_CONFIG

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


@main.command()
@click.option(
    "--book-dir",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Book output directory (must contain chunks.jsonl)",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "elevenlabs"]),
    default="openai",
    help="TTS provider",
)
@click.option(
    "--voice",
    default=None,
    help="Voice name (openai: alloy/echo/fable/onyx/nova/shimmer) or voice_id (elevenlabs)",
)
@click.option(
    "--model",
    "tts_model",
    default=None,
    help="Model name (openai: tts-1/tts-1-hd, elevenlabs: eleven_multilingual_v2)",
)
@click.option("--resume", is_flag=True, help="Resume interrupted processing")
@click.option("--concurrency", default=5, help="Max parallel API requests")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def tts(
    book_dir: Path,
    provider: str,
    voice: str | None,
    tts_model: str | None,
    resume: bool,
    concurrency: int,
    verbose: bool,
) -> None:
    """Generate audio for each chunk using TTS."""
    setup_logging(verbose)

    # Derive book_id from directory name
    book_id = book_dir.name

    try:
        report = run_tts(
            book_dir=book_dir,
            book_id=book_id,
            provider_name=provider,
            voice=voice,
            model=tts_model,
            resume=resume,
            concurrency=concurrency,
        )
        duration_s = report.total_duration_ms // 1000
        click.echo(
            f"TTS completed: {report.completed_chunks}/{report.total_chunks} chunks, "
            f"{report.failed_chunks} failed, ~{duration_s}s total audio"
        )
    except PipelineError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--book-dir",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Book output directory (must contain chunks.jsonl)",
)
@click.option(
    "--model",
    "embedding_model",
    default=None,
    help="Embedding model (default: text-embedding-3-small)",
)
@click.option("--batch-size", default=100, help="Chunks per embedding API call")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def rag(
    book_dir: Path,
    embedding_model: str | None,
    batch_size: int,
    verbose: bool,
) -> None:
    """Build RAG vector index from chunks."""
    setup_logging(verbose)
    book_id = book_dir.name

    try:
        report = run_rag(
            book_dir=book_dir,
            book_id=book_id,
            model=embedding_model,
            batch_size=batch_size,
        )
        click.echo(
            f"RAG completed: {report.vectors_indexed} vectors, "
            f"{report.dimensions}d, model={report.embedding_model}"
        )
    except PipelineError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--book-dir",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Book output directory (must contain chunks.jsonl)",
)
@click.option(
    "--model",
    "llm_model",
    default=None,
    help="LLM model for summaries (default: claude-sonnet-4-20250514)",
)
@click.option("--interval", default=50, help="Chunks between checkpoints (default: 50)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def memory(
    book_dir: Path,
    llm_model: str | None,
    interval: int,
    verbose: bool,
) -> None:
    """Generate memory checkpoints (story summaries + entity tracking)."""
    setup_logging(verbose)
    book_id = book_dir.name

    try:
        report = run_memory(
            book_dir=book_dir,
            book_id=book_id,
            model=llm_model,
            interval=interval,
        )
        click.echo(
            f"Memory completed: {report.checkpoints_generated} checkpoints, "
            f"model={report.llm_model}"
        )
    except PipelineError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
