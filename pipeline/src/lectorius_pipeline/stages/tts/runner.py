"""TTS stage runner — generate audio for each chunk."""

import asyncio
import json
import logging
import os
from pathlib import Path

from mutagen.mp3 import MP3

from lectorius_pipeline.errors import AudioWriteError, TTSError, TTSProviderError
from lectorius_pipeline.schemas import Chunk, PlaybackMapEntry, TTSReport

from .progress import TTSProgress
from .providers.base import TTSProvider
from .providers.elevenlabs import ElevenLabsTTS
from .providers.openai_tts import OpenAITTS

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0


def run_tts(
    book_dir: Path,
    book_id: str,
    provider_name: str = "openai",
    voice: str | None = None,
    model: str | None = None,
    resume: bool = False,
    concurrency: int = 5,
) -> TTSReport:
    """Run the TTS stage.

    Args:
        book_dir: Path to book output directory.
        book_id: Book identifier.
        provider_name: TTS provider ('openai' or 'elevenlabs').
        voice: Voice name/ID (provider-specific). Uses provider default if None.
        model: Model name. Uses provider default if None.
        resume: If True, skip already-completed chunks.
        concurrency: Max parallel API requests.

    Returns:
        TTSReport with processing stats.

    Raises:
        TTSError: If the stage fails critically.
    """
    logger.info("Starting TTS stage for %s (provider=%s)", book_id, provider_name)

    # Load chunks
    chunks = _load_chunks(book_dir)
    logger.info("Loaded %d chunks for TTS", len(chunks))

    # Create provider
    provider = _create_provider(provider_name, voice, model)
    logger.info("Using %s provider (voice=%s, model=%s)", provider.name, provider.voice, provider.model)

    # Setup audio output directory
    audio_dir = book_dir / "audio" / "chunks"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Load progress
    progress = TTSProgress(book_dir)
    if resume:
        progress.load()
        logger.info("Resuming: %d chunks already completed", progress.completed_count)

    # Filter to pending chunks
    pending = [c for c in chunks if c.chunk_id not in progress.completed_ids]
    logger.info("Processing %d pending chunks (concurrency=%d)", len(pending), concurrency)

    # Run async processing
    asyncio.run(_process_chunks(pending, provider, audio_dir, progress, concurrency))

    # Build playback map
    playback_entries = _build_playback_map(chunks, progress, book_dir)

    # Write playback_map.jsonl
    _write_playback_map(book_dir, playback_entries)

    # Build report
    report = TTSReport(
        success=progress.failed_count == 0,
        book_id=book_id,
        provider=provider.name,
        voice=provider.voice,
        model=provider.model,
        total_chunks=len(chunks),
        completed_chunks=progress.completed_count,
        failed_chunks=progress.failed_count,
        total_duration_ms=progress.total_duration_ms(),
        warnings=[f"Failed chunk: {e.chunk_id} — {e.error}" for e in progress.failed_entries],
        errors=[],
    )

    # Write report
    reports_dir = book_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "tts.json"
    report_path.write_text(report.model_dump_json(indent=2))

    logger.info(
        "TTS stage completed: %d/%d chunks, %d failed, total duration %ds",
        progress.completed_count,
        len(chunks),
        progress.failed_count,
        progress.total_duration_ms() // 1000,
    )

    if progress.failed_count > 0:
        logger.warning(
            "%d chunks failed TTS. Re-run with --resume to retry.",
            progress.failed_count,
        )

    return report


def _load_chunks(book_dir: Path) -> list[Chunk]:
    """Load chunks from chunks.jsonl."""
    chunks_path = book_dir / "chunks.jsonl"
    if not chunks_path.exists():
        raise TTSError(f"chunks.jsonl not found in {book_dir}")

    chunks: list[Chunk] = []
    with open(chunks_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(Chunk.model_validate_json(line))

    if not chunks:
        raise TTSError("chunks.jsonl is empty")

    return chunks


def _create_provider(
    provider_name: str,
    voice: str | None,
    model: str | None,
) -> TTSProvider:
    """Create a TTS provider instance from name and config."""
    if provider_name == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise TTSError("OPENAI_API_KEY environment variable not set")
        kwargs: dict = {"api_key": api_key}
        if voice:
            kwargs["voice"] = voice
        if model:
            kwargs["model"] = model
        return OpenAITTS(**kwargs)

    elif provider_name == "elevenlabs":
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise TTSError("ELEVENLABS_API_KEY environment variable not set")
        voice_id = voice or os.environ.get("ELEVENLABS_VOICE_ID")
        if not voice_id:
            raise TTSError(
                "Voice ID required for ElevenLabs. Pass --voice or set ELEVENLABS_VOICE_ID"
            )
        kwargs = {"api_key": api_key, "voice_id": voice_id}
        if model:
            kwargs["model"] = model
        return ElevenLabsTTS(**kwargs)

    else:
        raise TTSError(f"Unknown TTS provider: {provider_name}")


async def _process_chunks(
    chunks: list[Chunk],
    provider: TTSProvider,
    audio_dir: Path,
    progress: TTSProgress,
    concurrency: int,
) -> None:
    """Process chunks with bounded concurrency."""
    if not chunks:
        return

    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(chunk: Chunk) -> None:
        async with semaphore:
            await _synthesize_chunk(chunk, provider, audio_dir, progress)

    tasks = [process_one(chunk) for chunk in chunks]
    await asyncio.gather(*tasks)


async def _synthesize_chunk(
    chunk: Chunk,
    provider: TTSProvider,
    audio_dir: Path,
    progress: TTSProgress,
) -> None:
    """Synthesize a single chunk with retry logic."""
    audio_path = audio_dir / f"{chunk.chunk_id}.mp3"
    relative_path = f"audio/chunks/{chunk.chunk_id}.mp3"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            audio_bytes = await provider.synthesize(chunk.text)

            # Write to disk
            try:
                audio_path.write_bytes(audio_bytes)
            except OSError as e:
                raise AudioWriteError(f"Failed to write {audio_path}: {e}") from e

            # Get duration
            duration_ms = _get_duration_ms(audio_path)

            progress.record_success(chunk.chunk_id, relative_path, duration_ms)
            logger.debug(
                "Chunk %s: %dms (%d bytes)",
                chunk.chunk_id,
                duration_ms,
                len(audio_bytes),
            )
            return

        except AudioWriteError:
            # Don't retry disk errors
            raise

        except Exception as e:
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "Chunk %s attempt %d/%d failed: %s. Retrying in %.1fs...",
                    chunk.chunk_id,
                    attempt,
                    MAX_RETRIES,
                    str(e),
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                error_msg = f"Failed after {MAX_RETRIES} attempts: {e}"
                logger.error("Chunk %s: %s", chunk.chunk_id, error_msg)
                progress.record_failure(chunk.chunk_id, error_msg)


def _get_duration_ms(audio_path: Path) -> int:
    """Get duration of an mp3 file in milliseconds using mutagen."""
    try:
        audio = MP3(audio_path)
        return int(audio.info.length * 1000)
    except Exception as e:
        logger.warning("Could not read duration for %s: %s", audio_path.name, e)
        return -1


def _build_playback_map(
    chunks: list[Chunk],
    progress: TTSProgress,
    book_dir: Path,
) -> list[PlaybackMapEntry]:
    """Build sorted playback map from progress data."""
    entries: list[PlaybackMapEntry] = []

    for chunk in chunks:
        if chunk.chunk_id not in progress.completed_ids:
            continue

        completed = [
            e for e in progress.completed_entries if e.chunk_id == chunk.chunk_id
        ][0]

        entries.append(
            PlaybackMapEntry(
                chunk_id=chunk.chunk_id,
                chapter_id=chunk.chapter_id,
                chunk_index=chunk.chunk_index,
                audio_path=completed.audio_path or "",
                duration_ms=completed.duration_ms or 0,
                start_ms=0,
                end_ms=completed.duration_ms or 0,
            )
        )

    # Sort by chunk_index
    entries.sort(key=lambda e: e.chunk_index)
    return entries


def _write_playback_map(book_dir: Path, entries: list[PlaybackMapEntry]) -> None:
    """Write playback_map.jsonl."""
    map_path = book_dir / "playback_map.jsonl"
    with open(map_path, "w") as f:
        for entry in entries:
            f.write(entry.model_dump_json() + "\n")
    logger.info("Wrote %d playback map entries", len(entries))
