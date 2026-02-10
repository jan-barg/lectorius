"""ElevenLabs TTS provider."""

import logging

import httpx

from .base import TTSProvider

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "eleven_multilingual_v2"
API_BASE = "https://api.elevenlabs.io/v1/text-to-speech"


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs text-to-speech provider.

    Production-quality voice synthesis. Requires a voice_id from the
    ElevenLabs dashboard. Cost is quota-based (~$300/1M chars equivalent).
    """

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model: str = DEFAULT_MODEL,
    ) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model = model

    @property
    def name(self) -> str:
        return "elevenlabs"

    @property
    def voice(self) -> str:
        return self._voice_id

    @property
    def model(self) -> str:
        return self._model

    async def synthesize(self, text: str) -> bytes:
        """Generate mp3 audio from text using ElevenLabs API."""
        url = f"{API_BASE}/{self._voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self._model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            return response.content
