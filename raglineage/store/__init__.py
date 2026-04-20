"""Vector store implementations."""

from raglineage.store.base import BaseVectorStore
from raglineage.store.mapping import LNMapping
from raglineage.store.numpy_store import NumpyStore

try:
    from raglineage.store.faiss_store import FAISSStore  # noqa: F401
except Exception:  # pragma: no cover
    # Optional dependency / native import issues (e.g. faiss not installed).
    FAISSStore = None  # type: ignore

__all__ = ["BaseVectorStore", "FAISSStore", "NumpyStore", "LNMapping"]
