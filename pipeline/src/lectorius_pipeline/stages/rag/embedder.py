"""OpenAI embedding client for RAG stage."""

import logging

from openai import OpenAI

from lectorius_pipeline.errors import EmbeddingError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "text-embedding-3-small"
DEFAULT_BATCH_SIZE = 100


class Embedder:
    """Batch embedding client using OpenAI embeddings API."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._batch_size = batch_size

    @property
    def model(self) -> str:
        return self._model

    @property
    def batch_size(self) -> int:
        return self._batch_size

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (one per input text).

        Raises:
            EmbeddingError: If the API call fails.
        """
        if not texts:
            return []

        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=texts,
            )
            # Sort by index to guarantee order matches input
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except Exception as e:
            raise EmbeddingError(
                f"Embedding API call failed for batch of {len(texts)}: {e}"
            ) from e
