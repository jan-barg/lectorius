"""Chunkify stage runner."""

import logging
from pathlib import Path

from lectorius_pipeline.config import ChunkConfig, PipelineConfig
from lectorius_pipeline.errors import ChunkTooLargeError, OffsetMismatchError
from lectorius_pipeline.schemas import Chapter, Chunk, ChunkifyReport, Manifest

from .splitter import (
    ends_with_sentence_punctuation,
    load_spacy_model,
    split_into_sentences_regex,
    split_into_sentences_spacy,
    split_text_into_paragraphs,
    unwrap_hard_wrapped_lines,
)

logger = logging.getLogger(__name__)


def run_chunkify(output_dir: Path, book_id: str, config: PipelineConfig) -> ChunkifyReport:
    """
    Run the chunkify stage.

    Splits text into chunks of approximately target_chars size.

    Args:
        output_dir: Book output directory
        book_id: Book identifier
        config: Pipeline configuration

    Returns:
        ChunkifyReport with processing results
    """
    logger.info("Starting chunkify stage for %s", book_id)
    chunk_config = config.chunking

    # Load text and chapters
    raw_text = (output_dir / "raw_text.txt").read_text(encoding="utf-8")
    chapters = _load_chapters(output_dir)

    # Try to load spacy
    nlp = None
    splitter_used = "regex"
    if chunk_config.sentence_splitter == "spacy":
        nlp = load_spacy_model(chunk_config.spacy_model)
        if nlp:
            splitter_used = "spacy"

    warnings: list[str] = []
    if chunk_config.sentence_splitter == "spacy" and nlp is None:
        warnings.append("spacy unavailable, using regex sentence splitter")

    # Process each chapter
    all_chunks: list[Chunk] = []
    global_chunk_index = 0

    for chapter in chapters:
        chapter_text = raw_text[chapter.char_start : chapter.char_end]

        if not chapter_text.strip():
            warnings.append(f"Chapter {chapter.chapter_id} is empty, skipping")
            continue

        chapter_chunks, global_chunk_index = _chunkify_chapter(
            chapter_text=chapter_text,
            chapter=chapter,
            book_id=book_id,
            global_chunk_index=global_chunk_index,
            chunk_config=chunk_config,
            nlp=nlp,
        )

        all_chunks.extend(chapter_chunks)

    if not all_chunks:
        raise ChunkTooLargeError("No chunks produced from text")

    # Validate offsets
    _validate_chunk_offsets(all_chunks, raw_text)

    # Calculate stats
    chunk_sizes = [len(c.text) for c in all_chunks]
    avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0

    # Write outputs
    _write_chunks(output_dir, all_chunks)
    _update_manifest(output_dir, len(all_chunks))

    report = ChunkifyReport(
        success=True,
        book_id=book_id,
        total_chunks=len(all_chunks),
        avg_chunk_chars=round(avg_size, 1),
        min_chunk_chars=min(chunk_sizes) if chunk_sizes else 0,
        max_chunk_chars=max(chunk_sizes) if chunk_sizes else 0,
        sentence_splitter_used=splitter_used,
        warnings=warnings,
    )
    _write_report(output_dir / "reports", report)

    logger.info("Chunkify stage completed: %d chunks", len(all_chunks))
    return report


def _load_chapters(output_dir: Path) -> list[Chapter]:
    """Load chapters from chapters.jsonl."""
    path = output_dir / "chapters.jsonl"
    chapters: list[Chapter] = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        if line:
            chapters.append(Chapter.model_validate_json(line))
    return chapters


def _chunkify_chapter(
    chapter_text: str,
    chapter: Chapter,
    book_id: str,
    global_chunk_index: int,
    chunk_config: ChunkConfig,
    nlp,
) -> tuple[list[Chunk], int]:
    """
    Chunkify a single chapter.

    Strategy:
    - Split at paragraph breaks first (preferred)
    - Only split within paragraphs when needed for size
    - Preserve \n\n between paragraphs in chunk text
    - Target ~600 chars, not waiting until max (1600)
    - CRITICAL: Every chunk must end with sentence-ending punctuation

    Returns:
        Tuple of (chunks, updated_global_chunk_index)
    """
    # Split into paragraphs
    paragraphs = split_text_into_paragraphs(chapter_text)

    # Process paragraphs - unwrap hard-wrapped lines
    processed_paragraphs: list[str] = []
    for para in paragraphs:
        processed_paragraphs.append(unwrap_hard_wrapped_lines(para))

    # Build chunks using paragraph-aware packing
    chunks: list[Chunk] = []
    current_paragraphs: list[str] = []
    current_len = 0
    current_start = chapter.char_start
    para_idx = 0

    while para_idx < len(processed_paragraphs):
        para = processed_paragraphs[para_idx]
        para_len = len(para)

        # If single paragraph exceeds target, we need to split it
        if para_len > chunk_config.target_chars and not current_paragraphs:
            # Split large paragraph into sentences
            if nlp:
                sentences = split_into_sentences_spacy(para, nlp)
            else:
                sentences = split_into_sentences_regex(para)

            if not sentences:
                sentences = [para]  # fallback

            # Pack sentences into chunks (sentence packing already ensures boundaries)
            sentence_chunks = _pack_sentences_into_chunks(
                sentences=sentences,
                book_id=book_id,
                chapter_id=chapter.chapter_id,
                chunk_config=chunk_config,
                global_chunk_index=global_chunk_index,
                char_start=current_start,
            )

            if sentence_chunks:
                chunks.extend(sentence_chunks)
                global_chunk_index = sentence_chunks[-1].chunk_index
                current_start = sentence_chunks[-1].char_end

            para_idx += 1
            continue

        # Would adding this paragraph (with \n\n separator) exceed target?
        separator_len = 2 if current_paragraphs else 0  # \n\n
        potential_len = current_len + separator_len + para_len

        if potential_len > chunk_config.target_chars and current_paragraphs:
            # Check if current chunk ends with sentence punctuation
            chunk_text = "\n\n".join(current_paragraphs)

            if ends_with_sentence_punctuation(chunk_text):
                # Safe to emit
                global_chunk_index += 1
                chunk = _create_chunk(
                    text=chunk_text,
                    book_id=book_id,
                    chapter_id=chapter.chapter_id,
                    chunk_index=global_chunk_index,
                    char_start=current_start,
                )
                chunks.append(chunk)
                current_start = chunk.char_end
                current_paragraphs = []
                current_len = 0
                # Don't increment para_idx - we still need to process current para
                continue
            else:
                # Current chunk doesn't end with sentence punctuation
                # Include this paragraph even if we exceed target (up to max)
                combined_len = current_len + separator_len + para_len
                if combined_len <= chunk_config.max_chars:
                    current_paragraphs.append(para)
                    current_len = combined_len
                    para_idx += 1
                    continue
                else:
                    # Would exceed max - emit anyway (edge case)
                    logger.warning(
                        "Chunk doesn't end with sentence punctuation but at max size"
                    )
                    global_chunk_index += 1
                    chunk = _create_chunk(
                        text=chunk_text,
                        book_id=book_id,
                        chapter_id=chapter.chapter_id,
                        chunk_index=global_chunk_index,
                        char_start=current_start,
                    )
                    chunks.append(chunk)
                    current_start = chunk.char_end
                    current_paragraphs = []
                    current_len = 0
                    continue

        # Add paragraph to current batch
        current_paragraphs.append(para)
        current_len += separator_len + para_len
        para_idx += 1

    # Emit final chunk (final chunk is allowed to not end with sentence punctuation)
    if current_paragraphs:
        global_chunk_index += 1
        chunk_text = "\n\n".join(current_paragraphs)
        chunk = _create_chunk(
            text=chunk_text,
            book_id=book_id,
            chapter_id=chapter.chapter_id,
            chunk_index=global_chunk_index,
            char_start=current_start,
        )
        chunks.append(chunk)

    # Merge tiny chunks (threshold is now 200 chars)
    chunks = _merge_tiny_chunks(chunks, book_id, chunk_config)

    return chunks, global_chunk_index


def _pack_sentences_into_chunks(
    sentences: list[str],
    book_id: str,
    chapter_id: str,
    chunk_config: ChunkConfig,
    global_chunk_index: int,
    char_start: int,
) -> list[Chunk]:
    """Pack sentences into chunks targeting target_chars size."""
    chunks: list[Chunk] = []
    current_text = ""

    for sentence in sentences:
        # Would adding this sentence exceed target?
        separator = " " if current_text else ""
        potential_len = len(current_text) + len(separator) + len(sentence)

        if potential_len > chunk_config.target_chars and current_text:
            # Emit current chunk
            global_chunk_index += 1
            chunk = _create_chunk(
                text=current_text,
                book_id=book_id,
                chapter_id=chapter_id,
                chunk_index=global_chunk_index,
                char_start=char_start,
            )
            chunks.append(chunk)
            char_start = chunk.char_end
            current_text = sentence
        else:
            current_text = current_text + separator + sentence if current_text else sentence

    # Emit final chunk
    if current_text:
        global_chunk_index += 1
        chunk = _create_chunk(
            text=current_text,
            book_id=book_id,
            chapter_id=chapter_id,
            chunk_index=global_chunk_index,
            char_start=char_start,
        )
        chunks.append(chunk)

    return chunks


def _create_chunk(
    text: str,
    book_id: str,
    chapter_id: str,
    chunk_index: int,
    char_start: int,
) -> Chunk:
    """Create a Chunk object."""
    chunk_id = f"{chapter_id}_{chunk_index:06d}"
    return Chunk(
        book_id=book_id,
        chapter_id=chapter_id,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        text=text,
        char_start=char_start,
        char_end=char_start + len(text),
    )


def _merge_tiny_chunks(
    chunks: list[Chunk],
    book_id: str,
    chunk_config: ChunkConfig,
) -> list[Chunk]:
    """Merge chunks smaller than min_chars with neighbors."""
    if len(chunks) <= 1:
        return chunks

    merged: list[Chunk] = []

    for chunk in chunks:
        if len(chunk.text) < chunk_config.min_chars and merged:
            # Merge with previous, using \n\n to preserve paragraph separation
            prev = merged[-1]
            combined_text = prev.text + "\n\n" + chunk.text

            # Only merge if it won't exceed max
            if len(combined_text) <= chunk_config.max_chars:
                merged[-1] = Chunk(
                    book_id=book_id,
                    chapter_id=prev.chapter_id,
                    chunk_id=prev.chunk_id,
                    chunk_index=prev.chunk_index,
                    text=combined_text,
                    char_start=prev.char_start,
                    char_end=chunk.char_end,
                )
            else:
                merged.append(chunk)
        else:
            merged.append(chunk)

    # Re-index chunks to ensure sequential indices after merging
    reindexed: list[Chunk] = []
    for i, chunk in enumerate(merged, start=1):
        chunk_id = f"{chunk.chapter_id}_{i:06d}"
        reindexed.append(Chunk(
            book_id=chunk.book_id,
            chapter_id=chunk.chapter_id,
            chunk_id=chunk_id,
            chunk_index=i,
            text=chunk.text,
            char_start=chunk.char_start,
            char_end=chunk.char_end,
        ))

    return reindexed


def _validate_chunk_offsets(chunks: list[Chunk], raw_text: str) -> None:
    """Validate that chunk offsets are sequential and don't overlap."""
    for i, chunk in enumerate(chunks):
        if chunk.char_end > len(raw_text):
            raise OffsetMismatchError(
                f"Chunk {chunk.chunk_id} char_end ({chunk.char_end}) "
                f"exceeds text length ({len(raw_text)})"
            )

        if i > 0:
            prev = chunks[i - 1]
            if chunk.char_start < prev.char_end:
                raise OffsetMismatchError(
                    f"Chunk {chunk.chunk_id} overlaps with {prev.chunk_id}"
                )


def _write_chunks(output_dir: Path, chunks: list[Chunk]) -> None:
    """Write chunks.jsonl."""
    path = output_dir / "chunks.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk.model_dump_json() + "\n")
    logger.debug("Wrote %s", path)


def _update_manifest(output_dir: Path, chunk_count: int) -> None:
    """Update manifest.json with chunkify stage."""
    path = output_dir / "manifest.json"
    manifest = Manifest.model_validate_json(path.read_text())

    if "chunkify" not in manifest.stages_completed:
        manifest.stages_completed.append("chunkify")
    manifest.stats.chunks = chunk_count

    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Updated %s", path)


def _write_report(reports_dir: Path, report: ChunkifyReport) -> None:
    """Write chunks.json report."""
    path = reports_dir / "chunks.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Wrote %s", path)
