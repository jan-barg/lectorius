"""TTS progress tracking for resumability."""

import json
import logging
from pathlib import Path

from lectorius_pipeline.schemas import TTSChunkProgress

logger = logging.getLogger(__name__)

PROGRESS_FILENAME = "tts_progress.jsonl"


class TTSProgress:
    """Track TTS processing progress for resumability.

    Stores one JSONL record per chunk. On resume, loads completed chunk IDs
    so they can be skipped.
    """

    def __init__(self, book_dir: Path) -> None:
        self._path = book_dir / "reports" / PROGRESS_FILENAME
        self._completed: dict[str, TTSChunkProgress] = {}
        self._failed: dict[str, TTSChunkProgress] = {}

    @property
    def completed_ids(self) -> set[str]:
        """Chunk IDs that completed successfully."""
        return set(self._completed.keys())

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    @property
    def failed_count(self) -> int:
        return len(self._failed)

    @property
    def completed_entries(self) -> list[TTSChunkProgress]:
        """All completed progress entries."""
        return list(self._completed.values())

    @property
    def failed_entries(self) -> list[TTSChunkProgress]:
        """All failed progress entries."""
        return list(self._failed.values())

    def load(self) -> None:
        """Load existing progress from disk."""
        if not self._path.exists():
            logger.info("No existing TTS progress found")
            return

        count = 0
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = TTSChunkProgress.model_validate_json(line)
                if entry.status == "completed":
                    self._completed[entry.chunk_id] = entry
                else:
                    self._failed[entry.chunk_id] = entry
                count += 1

        logger.info(
            "Loaded TTS progress: %d completed, %d failed",
            len(self._completed),
            len(self._failed),
        )

    def record_success(
        self,
        chunk_id: str,
        audio_path: str,
        duration_ms: int,
    ) -> None:
        """Record a successfully processed chunk."""
        entry = TTSChunkProgress(
            chunk_id=chunk_id,
            status="completed",
            audio_path=audio_path,
            duration_ms=duration_ms,
        )
        self._completed[chunk_id] = entry
        # Remove from failed if it was retried
        self._failed.pop(chunk_id, None)
        self._append(entry)

    def record_failure(self, chunk_id: str, error: str) -> None:
        """Record a failed chunk."""
        entry = TTSChunkProgress(
            chunk_id=chunk_id,
            status="failed",
            error=error,
        )
        self._failed[chunk_id] = entry
        self._append(entry)

    def _append(self, entry: TTSChunkProgress) -> None:
        """Append a progress entry to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a") as f:
            f.write(entry.model_dump_json() + "\n")

    def total_duration_ms(self) -> int:
        """Sum of durations for all completed chunks."""
        return sum(
            e.duration_ms for e in self._completed.values() if e.duration_ms is not None
        )
