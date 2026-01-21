"""Embedding backends."""

from raglineage.embedding.base import BaseEmbedder
from raglineage.embedding.local import LocalEmbedder

__all__ = ["BaseEmbedder", "LocalEmbedder"]

try:
    from raglineage.embedding.openai import OpenAIEmbedder

    __all__.append("OpenAIEmbedder")
except ImportError:
    pass
