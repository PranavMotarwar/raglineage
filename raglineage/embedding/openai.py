"""OpenAI embedding backend (optional, requires openai package)."""

from typing import Any

import numpy as np

from raglineage.embedding.base import BaseEmbedder
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedding backend."""

    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str | None = None) -> None:
        """
        Initialize OpenAI embedder.

        Args:
            model_name: OpenAI embedding model name
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        """
        if OpenAI is None:
            raise ImportError("openai package not installed. Install with: pip install raglineage[openai]")

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self._dimension: int | None = None

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text."""
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return np.array(response.data[0].embedding)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts."""
        response = self.client.embeddings.create(model=self.model_name, input=texts)
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        if self._dimension is None:
            # Get dimension by embedding a dummy text
            dummy_embedding = self.embed("dummy")
            self._dimension = len(dummy_embedding)
        return self._dimension
