"""Local embedding backend using sentence-transformers."""

from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from raglineage.embedding.base import BaseEmbedder
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "all-MiniLM-L6-v2"


class LocalEmbedder(BaseEmbedder):
    """Local embedder using sentence-transformers."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        """
        Initialize local embedder.

        Args:
            model_name: Sentence-transformer model name
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model: SentenceTransformer = SentenceTransformer(model_name)
        self._dimension: int | None = None

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text."""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts."""
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        if self._dimension is None:
            # Get dimension by embedding a dummy text
            dummy_embedding = self.embed("dummy")
            self._dimension = len(dummy_embedding)
        return self._dimension
