"""Local embedding backend using sentence-transformers."""

from __future__ import annotations

import hashlib
import re
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from raglineage.embedding.base import BaseEmbedder
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class LocalEmbedder(BaseEmbedder):
    """Local embedder using sentence-transformers."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        """
        Initialize local embedder.

        Args:
            model_name: Sentence-transformer model name
        """
        self._dimension: Optional[int] = None
        self._fallback = False
        self._fallback_dim = 384

        logger.info(f"Loading embedding model: {model_name}")
        try:
            self.model: SentenceTransformer | None = SentenceTransformer(model_name)
        except Exception as e:
            # Useful in offline / restricted environments (and makes tests resilient).
            self.model = None
            self._fallback = True
            logger.warning(
                f"Failed to load sentence-transformers model '{model_name}'. "
                f"Falling back to deterministic hash embeddings. Error: {e}"
            )

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text."""
        if self.model is not None:
            return self.model.encode(text, convert_to_numpy=True)
        return self._hash_embed(text)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts."""
        if self.model is not None:
            return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return np.vstack([self._hash_embed(t) for t in texts])

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        if self._dimension is None:
            if self.model is None:
                self._dimension = self._fallback_dim
            else:
                dummy_embedding = self.embed("dummy")
                self._dimension = len(dummy_embedding)
        return self._dimension

    def _hash_embed(self, text: str) -> np.ndarray:
        """Deterministic, offline fallback embedding.

        Not meant for production quality retrieval, but useful for demos/tests
        and environments without model downloads.
        """
        # Signed feature hashing preserves shared word features, unlike hashing
        # the entire document into an unrelated random vector. This remains a
        # lightweight fallback, but provides useful lexical retrieval offline.
        v = np.zeros(self._fallback_dim, dtype=np.float32)
        tokens = re.findall(r"[\w'-]+", text.casefold())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self._fallback_dim
            sign = 1.0 if digest[4] & 1 else -1.0
            v[index] += sign
        # Normalize to unit length for cosine-like behavior
        n = float(np.linalg.norm(v)) or 1.0
        return v / n
