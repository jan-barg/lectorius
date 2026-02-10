"""Abstract base class for TTS providers."""

from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Base class for text-to-speech providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'openai', 'elevenlabs')."""
        ...

    @property
    @abstractmethod
    def voice(self) -> str:
        """Voice identifier used for this provider."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier used for this provider."""
        ...

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Generate audio from text, return mp3 bytes."""
        ...
