"""Fallback audio generation — per-voice fallback clips for error/refusal responses."""

import asyncio
import logging
import os
from pathlib import Path

from supabase import create_client

from lectorius_pipeline.errors import FallbacksError
from lectorius_pipeline.stages.tts import create_provider
from lectorius_pipeline.stages.tts.providers.base import TTSProvider
from lectorius_pipeline.utils.io import load_book_meta

logger = logging.getLogger(__name__)

FALLBACKS = [
    {"id": "no_context_yet", "text": "I don't have enough context yet. Let's keep reading."},
    {"id": "error", "text": "I can't seem to find an answer right now."},
    {"id": "book_only", "text": "I can only help with questions about this book."},
]

STORAGE_BUCKET = "system"


def run_fallbacks(
    book_dir: Path | None = None,
    provider_name: str | None = None,
    voice: str | None = None,
    model: str | None = None,
) -> dict[str, bool]:
    """Generate and upload per-voice fallback audio files.

    Resolution: explicit flags > book.json > error.

    Args:
        book_dir: Optional path to book directory (reads book.json for voice/provider).
        provider_name: TTS provider name. Overrides book.json.
        voice: Voice ID. Overrides book.json.
        model: Model name. Uses provider default if None.

    Returns:
        Dict mapping fallback ID to whether it was generated (True) or already existed (False).

    Raises:
        FallbacksError: If required parameters cannot be resolved.
    """
    # Resolve voice and provider from book.json if not explicitly given
    book_meta = None
    if book_dir:
        book_meta = load_book_meta(book_dir)

    effective_provider = provider_name or (book_meta.tts_provider if book_meta else None)
    effective_voice = voice or (book_meta.voice_id if book_meta else None)

    if not effective_provider:
        raise FallbacksError("No provider specified and none found in book.json")
    if not effective_voice:
        raise FallbacksError("No voice specified and none found in book.json")

    logger.info(
        "Generating fallbacks for voice=%s (provider=%s)",
        effective_voice,
        effective_provider,
    )

    # Create TTS provider
    provider = create_provider(effective_provider, effective_voice, model)

    # Create Supabase client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise FallbacksError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    supabase = create_client(supabase_url, supabase_key)

    # Generate and upload missing fallback audio
    results = asyncio.run(_generate_and_upload(provider, effective_voice, supabase))

    generated = sum(1 for v in results.values() if v)
    skipped = sum(1 for v in results.values() if not v)
    logger.info("Fallbacks complete: %d generated, %d already existed", generated, skipped)

    return results


async def _generate_and_upload(
    provider: TTSProvider,
    voice_id: str,
    supabase: object,
) -> dict[str, bool]:
    """Generate and upload missing fallback audio files."""
    results: dict[str, bool] = {}

    for fb in FALLBACKS:
        remote_path = f"fallback-audio/{voice_id}/{fb['id']}.mp3"

        # Check if already exists in Supabase Storage
        if _exists_in_storage(supabase, remote_path):
            logger.info("Fallback '%s' already exists for voice %s, skipping", fb["id"], voice_id)
            results[fb["id"]] = False
            continue

        # Generate audio
        logger.info("Generating fallback '%s' for voice %s...", fb["id"], voice_id)
        audio_bytes = await provider.synthesize(fb["text"])

        # Upload to Supabase Storage
        _upload_to_storage(supabase, remote_path, audio_bytes)
        logger.info("Uploaded fallback '%s' (%d bytes)", fb["id"], len(audio_bytes))
        results[fb["id"]] = True

    return results


def _exists_in_storage(supabase: object, remote_path: str) -> bool:
    """Check if a file exists in Supabase Storage."""
    try:
        parts = remote_path.rsplit("/", 1)
        folder = parts[0] if len(parts) > 1 else ""
        filename = parts[1] if len(parts) > 1 else parts[0]

        result = supabase.storage.from_(STORAGE_BUCKET).list(folder)  # type: ignore[union-attr]
        return any(f["name"] == filename for f in result)
    except Exception:
        return False


def _upload_to_storage(supabase: object, remote_path: str, data: bytes) -> None:
    """Upload a file to Supabase Storage."""
    supabase.storage.from_(STORAGE_BUCKET).upload(  # type: ignore[union-attr]
        remote_path,
        data,
        {"content-type": "audio/mpeg"},
    )
