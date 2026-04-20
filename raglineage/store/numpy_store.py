"""NumPy-based vector store (pure Python fallback).

This is a small, dependency-light fallback for environments where FAISS is not
available. It uses cosine similarity over L2-normalized embeddings.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from raglineage.store.base import BaseVectorStore
from raglineage.store.mapping import LNMapping
from raglineage.utils.io import ensure_dir
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    x = x.astype("float32", copy=False)
    if x.ndim == 1:
        x = x.reshape(1, -1)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return x / norms


class NumpyStore(BaseVectorStore):
    """Brute-force cosine similarity store backed by NumPy arrays."""

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension
        self.mapping = LNMapping()
        self._vectors: np.ndarray = np.empty((0, dimension), dtype="float32")

    def add(self, ln_id: str, embedding: np.ndarray) -> None:
        embedding = _l2_normalize(embedding)
        if embedding.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embedding.shape[1]} != {self.dimension}")

        idx = self.mapping.add(ln_id)
        if idx < self._vectors.shape[0]:
            self._vectors[idx] = embedding[0]
        else:
            # Append
            self._vectors = np.vstack([self._vectors, embedding])

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[tuple[str, float]]:
        if self._vectors.shape[0] == 0:
            return []

        q = _l2_normalize(query_embedding)
        # Cosine similarity since vectors are normalized
        sims = (self._vectors @ q[0]).astype("float32", copy=False)
        top_k = min(int(k), sims.shape[0])
        # Argpartition for speed, then sort
        idxs = np.argpartition(-sims, top_k - 1)[:top_k]
        idxs = idxs[np.argsort(-sims[idxs])]

        results: list[tuple[str, float]] = []
        for idx in idxs:
            ln_id = self.mapping.get_ln_id(int(idx))
            if ln_id is None:
                continue
            results.append((ln_id, float(sims[int(idx)])))
        return results

    def remove(self, ln_id: str) -> None:
        # Keep vectors array stable; just remove mapping.
        self.mapping.remove(ln_id)

    def save(self, path: str) -> None:
        path = Path(path)
        ensure_dir(path.parent)

        vectors_path = path.with_suffix(".npy")
        mapping_path = path.parent / f"{path.stem}_mapping.json"
        meta_path = path.parent / f"{path.stem}_meta.json"

        np.save(str(vectors_path), self._vectors)
        self.mapping.save(str(mapping_path))
        from raglineage.utils.io import save_json

        save_json({"dimension": self.dimension, "count": int(self._vectors.shape[0])}, meta_path)

    def load(self, path: str) -> None:
        path = Path(path)
        vectors_path = path.with_suffix(".npy")
        mapping_path = path.parent / f"{path.stem}_mapping.json"

        if vectors_path.exists():
            self._vectors = np.load(str(vectors_path)).astype("float32", copy=False)
            self.dimension = int(self._vectors.shape[1]) if self._vectors.ndim == 2 else self.dimension
        else:
            logger.warning(f"Numpy vectors not found: {vectors_path}")
            self._vectors = np.empty((0, self.dimension), dtype="float32")

        self.mapping.load(str(mapping_path))

    def __len__(self) -> int:
        return int(self._vectors.shape[0])

