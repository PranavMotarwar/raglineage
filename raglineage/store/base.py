"""Base vector store interface."""

from abc import ABC, abstractmethod

import numpy as np


class BaseVectorStore(ABC):
    """Base interface for vector stores."""

    @abstractmethod
    def add(self, ln_id: str, embedding: np.ndarray) -> None:
        """
        Add an embedding with associated Lineage Node ID.

        Args:
            ln_id: Lineage Node ID
            embedding: Embedding vector
        """
        pass

    @abstractmethod
    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[tuple[str, float]]:
        """
        Search for similar embeddings.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return

        Returns:
            List of (ln_id, score) tuples
        """
        pass

    @abstractmethod
    def remove(self, ln_id: str) -> None:
        """
        Remove an embedding by Lineage Node ID.

        Args:
            ln_id: Lineage Node ID to remove
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Save store to disk."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load store from disk."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """Return number of vectors in store."""
        pass
