"""Shared I/O utilities for pipeline stages."""

import logging
from pathlib import Path

from lectorius_pipeline.errors import PipelineError
from lectorius_pipeline.schemas import BookMeta, Chunk, Manifest

logger = logging.getLogger(__name__)


def load_chunks(book_dir: Path, error_class: type[PipelineError] = PipelineError) -> list[Chunk]:
    """Load chunks from chunks.jsonl.

    Args:
        book_dir: Path to book output directory.
        error_class: Exception class to raise on failure.

    Returns:
        List of Chunk objects.

    Raises:
        error_class: If chunks.jsonl is missing or empty.
    """
    chunks_path = book_dir / "chunks.jsonl"
    if not chunks_path.exists():
        raise error_class(f"chunks.jsonl not found in {book_dir}")

    chunks: list[Chunk] = []
    with open(chunks_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(Chunk.model_validate_json(line))

    if not chunks:
        raise error_class("chunks.jsonl is empty")

    return chunks


def update_manifest(output_dir: Path, stage_name: str) -> None:
    """Append a stage to manifest.json stages_completed list.

    Args:
        output_dir: Book output directory containing manifest.json.
        stage_name: Stage name to append.
    """
    path = output_dir / "manifest.json"
    manifest = Manifest.model_validate_json(path.read_text())

    if stage_name not in manifest.stages_completed:
        manifest.stages_completed.append(stage_name)

    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")


def load_book_meta(book_dir: Path) -> BookMeta | None:
    """Load book metadata from book.json if available.

    Args:
        book_dir: Path to book output directory.

    Returns:
        BookMeta if book.json exists and is valid, None otherwise.
    """
    meta_path = book_dir / "book.json"
    if not meta_path.exists():
        return None
    try:
        return BookMeta.model_validate_json(meta_path.read_text())
    except Exception as e:
        logger.warning("Could not load book.json: %s", e)
        return None
