"""Base embedder interface."""

from abc import ABC, abstractmethod

import numpy as np


class BaseEmbedder(ABC):
    """Base interface for embedding models."""

    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Embed a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            Array of embedding vectors
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass
