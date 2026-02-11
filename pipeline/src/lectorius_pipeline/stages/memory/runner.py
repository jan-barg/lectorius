"""Memory stage runner — generate periodic story summaries."""

import json
import logging
import os
from pathlib import Path

from anthropic import Anthropic

from lectorius_pipeline.errors import CheckpointGenerationError, MemoryError_
from lectorius_pipeline.schemas import Chunk, MemoryReport

from .prompts import CHECKPOINT_PROMPT

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_INTERVAL = 50


def run_memory(
    book_dir: Path,
    book_id: str,
    model: str | None = None,
    interval: int = DEFAULT_INTERVAL,
) -> MemoryReport:
    """Run the memory stage: generate periodic story summaries.

    Args:
        book_dir: Path to book output directory.
        book_id: Book identifier.
        model: LLM model name. Defaults to claude-sonnet.
        interval: Chunks between checkpoints.

    Returns:
        MemoryReport with processing stats.

    Raises:
        MemoryError_: If the stage fails critically.
    """
    logger.info("Starting Memory stage for %s", book_id)

    # Load chunks
    chunks = _load_chunks(book_dir)
    total = len(chunks)
    logger.info("Loaded %d chunks for memory generation", total)

    # Create Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise MemoryError_("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)
    llm_model = model or DEFAULT_MODEL

    # Determine checkpoint positions
    positions = _compute_positions(total, interval)
    logger.info("Checkpoint positions: %s", positions)

    # Generate checkpoints
    checkpoints: list[dict] = []
    previous: dict | None = None
    last_end = 0
    warnings: list[str] = []

    for i, pos in enumerate(positions):
        section_chunks = chunks[last_end:pos]
        chunk_texts = "\n\n---\n\n".join(c.text for c in section_chunks)

        prev_json = json.dumps(previous, indent=2) if previous else "This is the first checkpoint."

        prompt = CHECKPOINT_PROMPT.format(
            previous_checkpoint=prev_json,
            start_chunk=last_end + 1,
            end_chunk=pos,
            chunk_texts=chunk_texts,
        )

        logger.info(
            "Generating checkpoint %d/%d (chunks %d-%d)",
            i + 1, len(positions), last_end + 1, pos,
        )

        try:
            data = _call_llm(client, llm_model, prompt)
        except CheckpointGenerationError as e:
            warning = f"Checkpoint {i + 1} failed: {e}"
            logger.warning(warning)
            warnings.append(warning)
            last_end = pos
            continue

        checkpoint = {
            "book_id": book_id,
            "checkpoint_index": i + 1,
            "until_chunk_index": pos,
            "until_chunk_id": chunks[pos - 1].chunk_id,
            "summary": data.get("summary", ""),
            "entities": data.get("entities", {"people": [], "places": [], "open_threads": []}),
        }

        checkpoints.append(checkpoint)
        previous = checkpoint
        last_end = pos

    # Write output
    memory_dir = book_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    checkpoints_path = memory_dir / "checkpoints.jsonl"
    with open(checkpoints_path, "w") as f:
        for cp in checkpoints:
            f.write(json.dumps(cp) + "\n")
    logger.info("Wrote %d checkpoints to checkpoints.jsonl", len(checkpoints))

    # Build report
    report = MemoryReport(
        success=len(checkpoints) > 0,
        book_id=book_id,
        llm_model=llm_model,
        total_chunks=total,
        checkpoints_generated=len(checkpoints),
        checkpoint_positions=positions,
        warnings=warnings,
    )

    # Write report
    reports_dir = book_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "memory.json"
    report_path.write_text(report.model_dump_json(indent=2))

    logger.info("Memory stage completed: %d checkpoints generated", len(checkpoints))
    return report


def _compute_positions(total: int, interval: int) -> list[int]:
    """Compute checkpoint positions.

    For small books (<100 chunks), checkpoint at 25%, 50%, 75%, 100%.
    Otherwise, every `interval` chunks plus the final position.
    """
    if total < 100:
        positions = [
            max(1, total // 4),
            max(1, total // 2),
            max(1, 3 * total // 4),
            total,
        ]
        # Deduplicate while preserving order
        seen: set[int] = set()
        unique: list[int] = []
        for p in positions:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique

    positions = list(range(interval, total + 1, interval))
    if not positions or positions[-1] != total:
        positions.append(total)
    return positions


def _call_llm(client: Anthropic, model: str, prompt: str) -> dict:
    """Call Claude and parse JSON response.

    Raises:
        CheckpointGenerationError: If the call fails or returns invalid JSON.
    """
    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text
    except Exception as e:
        raise CheckpointGenerationError(f"LLM API call failed: {e}") from e

    # Strip markdown code fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise CheckpointGenerationError(
            f"LLM returned invalid JSON: {e}\nRaw: {raw_text[:200]}"
        ) from e

    if "summary" not in data:
        raise CheckpointGenerationError(f"LLM response missing 'summary' key")

    return data


def _load_chunks(book_dir: Path) -> list[Chunk]:
    """Load chunks from chunks.jsonl."""
    chunks_path = book_dir / "chunks.jsonl"
    if not chunks_path.exists():
        raise MemoryError_(f"chunks.jsonl not found in {book_dir}")

    chunks: list[Chunk] = []
    with open(chunks_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(Chunk.model_validate_json(line))

    if not chunks:
        raise MemoryError_("chunks.jsonl is empty")

    return chunks
