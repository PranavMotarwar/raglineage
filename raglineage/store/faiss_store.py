"""FAISS-based vector store implementation."""

from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from raglineage.store.base import BaseVectorStore
from raglineage.store.mapping import LNMapping
from raglineage.utils.io import ensure_dir
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class FAISSStore(BaseVectorStore):
    """FAISS-based vector store."""

    def __init__(self, dimension: int) -> None:
        """
        Initialize FAISS store.

        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.mapping = LNMapping()
        self._initialize_index()

    def _initialize_index(self) -> None:
        """Initialize FAISS index."""
        # Use L2 distance (Euclidean)
        self.index = faiss.IndexFlatL2(self.dimension)

    def add(self, ln_id: str, embedding: np.ndarray) -> None:
        """Add an embedding."""
        if self.index is None:
            self._initialize_index()

        embedding = embedding.astype("float32")
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)

        idx = self.mapping.add(ln_id)
        # If index already exists, we need to handle it
        if idx < self.index.ntotal:
            # Update existing
            self.index.reconstruct(idx, embedding[0])
        else:
            # Add new
            self.index.add(embedding)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[tuple[str, float]]:
        """Search for similar embeddings."""
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = query_embedding.astype("float32")
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:  # FAISS returns -1 for invalid indices
                continue
            ln_id = self.mapping.get_ln_id(int(idx))
            if ln_id:
                # Convert L2 distance to similarity score (lower distance = higher similarity)
                score = 1.0 / (1.0 + float(dist))
                results.append((ln_id, score))

        return results

    def remove(self, ln_id: str) -> None:
        """Remove an embedding (FAISS doesn't support removal, so we mark it)."""
        # FAISS doesn't support removal, so we just remove from mapping
        # In a production system, you might want to rebuild the index
        self.mapping.remove(ln_id)
        logger.warning("FAISS doesn't support removal - consider rebuilding index")

    def save(self, path: str) -> None:
        """Save FAISS index and mapping to disk."""
        path = Path(path)
        ensure_dir(path.parent)

        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, str(path))

        # Save mapping
        mapping_path = path.parent / f"{path.stem}_mapping.json"
        self.mapping.save(str(mapping_path))

    def load(self, path: str) -> None:
        """Load FAISS index and mapping from disk."""
        path = Path(path)
        if not path.exists():
            logger.warning(f"FAISS index not found: {path}")
            return

        # Load FAISS index
        self.index = faiss.read_index(str(path))
        self.dimension = self.index.d

        # Load mapping
        mapping_path = path.parent / f"{path.stem}_mapping.json"
        self.mapping.load(str(mapping_path))

    def __len__(self) -> int:
        """Return number of vectors in store."""
        if self.index is None:
            return 0
        return self.index.ntotal
