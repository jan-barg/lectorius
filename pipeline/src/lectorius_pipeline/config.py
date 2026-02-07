"""Pipeline configuration."""

from dataclasses import dataclass, field


@dataclass
class ChunkConfig:
    """Chunking configuration."""

    target_chars: int = 600
    min_chars: int = 200
    max_chars: int = 1600
    sentence_splitter: str = "regex"  # "spacy" or "regex"
    spacy_model: str = "en_core_web_sm"


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""

    pipeline_version: str = "1.0.0"
    chunking: ChunkConfig = field(default_factory=ChunkConfig)
    min_text_length: int = 1000  # minimum chars for valid book


# Default configuration instance
DEFAULT_CONFIG = PipelineConfig()
