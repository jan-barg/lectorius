"""Pydantic schemas for pipeline data models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BookMeta(BaseModel):
    """Book metadata extracted from epub."""

    book_id: str
    title: str
    author: str | None = None
    language: str = "en"
    year: int | None = None
    book_type: Literal["fiction", "non-fiction", "biography"] = "fiction"
    source: str | None = None
    source_id: str | None = None


class ManifestConfig(BaseModel):
    """Pipeline configuration stored in manifest."""

    tts_voice_id: str = ""
    tts_model: str = ""
    chunk_target_chars: int = 600
    chunk_min_chars: int = 100
    chunk_max_chars: int = 1600
    checkpoint_interval_chunks: int = 50
    embedding_model: str = ""


class ManifestStats(BaseModel):
    """Statistics stored in manifest."""

    chapters: int = 0
    chunks: int = 0
    total_audio_duration_ms: int = 0
    total_chars: int = 0


class Manifest(BaseModel):
    """Book pack manifest with processing info."""

    book_id: str
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pipeline_version: str = "1.0.0"
    stages_completed: list[str] = Field(default_factory=list)
    config: ManifestConfig = Field(default_factory=ManifestConfig)
    stats: ManifestStats = Field(default_factory=ManifestStats)


class Chapter(BaseModel):
    """Chapter boundary with character offsets."""

    book_id: str
    chapter_id: str  # format: {book_id}_ch{index:03d}
    index: int  # 1-indexed
    title: str
    char_start: int  # inclusive offset in raw_text.txt
    char_end: int  # exclusive offset in raw_text.txt


class Chunk(BaseModel):
    """Atomic text unit for playback."""

    book_id: str
    chapter_id: str
    chunk_id: str  # format: {chapter_id}_{chunk_index:06d}
    chunk_index: int  # global 1-indexed position across entire book
    text: str
    char_start: int
    char_end: int


class IngestReport(BaseModel):
    """Report from ingest stage."""

    success: bool
    book_id: str
    source_path: str
    chars_extracted: int
    chars_after_cleanup: int
    gutenberg_markers_found: bool
    toc_detected: bool
    toc_char_range: tuple[int, int] | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ChapterizeReport(BaseModel):
    """Report from chapterize stage."""

    success: bool
    book_id: str
    chapters_detected: int
    pattern_matches: dict[str, int] = Field(default_factory=dict)
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ChunkifyReport(BaseModel):
    """Report from chunkify stage."""

    success: bool
    book_id: str
    total_chunks: int
    avg_chunk_chars: float
    min_chunk_chars: int
    max_chunk_chars: int
    sentence_splitter_used: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    """Single validation issue."""

    severity: Literal["ERROR", "WARN"]
    check: str
    message: str
    chunk_id: str | None = None
    chunk_index: int | None = None


class ValidateReport(BaseModel):
    """Report from validate stage."""

    success: bool
    book_id: str
    total_chunks: int
    issues: list[ValidationIssue] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
