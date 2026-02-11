"""Custom exceptions for pipeline stages."""


class PipelineError(Exception):
    """Base exception for all pipeline errors."""

    def __init__(self, message: str, stage: str | None = None) -> None:
        self.stage = stage
        super().__init__(message)


class IngestError(PipelineError):
    """Error during ingest stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="ingest")


class EpubParseError(IngestError):
    """Failed to parse epub file."""

    pass


class NoTextExtractedError(IngestError):
    """No text content extracted from epub."""

    pass


class SuspiciouslyShortError(IngestError):
    """Extracted text is suspiciously short."""

    pass


class LLMAssistError(IngestError):
    """LLM analysis failed (non-fatal)."""

    pass


class ChapterizeError(PipelineError):
    """Error during chapterize stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="chapterize")


class OverlappingChaptersError(ChapterizeError):
    """Chapter char ranges overlap."""

    pass


class ChunkifyError(PipelineError):
    """Error during chunkify stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="chunkify")


class ChunkTooLargeError(ChunkifyError):
    """Chunk exceeds maximum character limit."""

    pass


class OffsetMismatchError(ChunkifyError):
    """Chunk offsets do not match raw text."""

    pass


class TTSError(PipelineError):
    """Error during TTS stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="tts")


class TTSProviderError(TTSError):
    """TTS provider API call failed."""

    pass


class AudioWriteError(TTSError):
    """Failed to write audio file to disk."""

    pass


class ValidateError(PipelineError):
    """Error during validate stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="validate")


class ValidationFailedError(ValidateError):
    """Validation found critical errors."""

    def __init__(self, error_count: int) -> None:
        super().__init__(f"Validation failed with {error_count} error(s)")
        self.error_count = error_count


class RAGError(PipelineError):
    """Error during RAG stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="rag")


class EmbeddingError(RAGError):
    """Embedding API call failed."""

    pass


class MemoryError_(PipelineError):
    """Error during memory stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="memory")


class CheckpointGenerationError(MemoryError_):
    """Failed to generate a memory checkpoint."""

    pass
