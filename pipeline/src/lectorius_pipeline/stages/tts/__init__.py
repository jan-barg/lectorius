"""TTS stage — generate audio for each chunk."""

from .runner import create_provider, run_tts

__all__ = ["create_provider", "run_tts"]
