"""OpenAI TTS provider."""

import logging

from openai import AsyncOpenAI

from .base import TTSProvider

logger = logging.getLogger(__name__)

# Available voices: alloy, echo, fable, onyx, nova, shimmer
DEFAULT_VOICE = "alloy"
DEFAULT_MODEL = "tts-1"


class OpenAITTS(TTSProvider):
    """OpenAI text-to-speech provider.

    Uses the OpenAI TTS API. Good for development and testing (~$15/1M chars).
    For higher quality, use model="tts-1-hd" (~$30/1M chars).
    """

    def __init__(
        self,
        api_key: str,
        voice: str = DEFAULT_VOICE,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._voice = voice
        self._model = model

    @property
    def name(self) -> str:
        return "openai"

    @property
    def voice(self) -> str:
        return self._voice

    @property
    def model(self) -> str:
        return self._model

    async def synthesize(self, text: str) -> bytes:
        """Generate mp3 audio from text using OpenAI TTS API."""
        response = await self._client.audio.speech.create(
            model=self._model,
            voice=self._voice,
            input=text,
            response_format="mp3",
        )
        return response.content
