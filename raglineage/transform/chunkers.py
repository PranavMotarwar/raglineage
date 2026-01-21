"""Chunking strategies for splitting content."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterator

from raglineage.schemas.lineage_node import LineageNode
from raglineage.transform.base import BaseTransform
from raglineage.utils.hashing import compute_content_hash
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class ChunkingStrategy(ABC):
    """Base interface for chunking strategies."""

    @abstractmethod
    def chunk(self, content: str) -> list[str]:
        """
        Chunk content into pieces.

        Args:
            content: Content to chunk

        Returns:
            List of chunk strings
        """
        pass


class SimpleChunker(ChunkingStrategy):
    """Simple character-based chunker."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        """
        Initialize simple chunker.

        Args:
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, content: str) -> list[str]:
        """Chunk content by character count."""
        if len(content) <= self.chunk_size:
            return [content]

        chunks = []
        start = 0
        while start < len(content):
            end = start + self.chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - self.overlap
            if start >= len(content):
                break

        return chunks


class SemanticChunker(ChunkingStrategy):
    """Semantic chunker using sentence boundaries."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        """
        Initialize semantic chunker.

        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, content: str) -> list[str]:
        """Chunk content by sentences."""
        # Simple sentence splitting (can be enhanced with NLP libraries)
        sentences = content.replace(".\n", ". ").replace("\n", " ").split(". ")
        sentences = [s.strip() + "." for s in sentences if s.strip()]

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Overlap: keep last few sentences
                overlap_sentences = []
                overlap_size = 0
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break
                current_chunk = overlap_sentences
                current_size = overlap_size

            current_chunk.append(sentence)
            current_size += sentence_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else [content]


class SimpleChunkerTransform(BaseTransform):
    """Transform that applies simple chunking."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        """Initialize chunker transform."""
        self.chunker = SimpleChunker(chunk_size, overlap)

    @property
    def name(self) -> str:
        """Transform name."""
        return "simple_chunk"

    def transform(self, ln: LineageNode) -> Iterator[LineageNode]:
        """Chunk a Lineage Node into multiple nodes."""
        chunks = self.chunker.chunk(ln.content)
        for idx, chunk_content in enumerate(chunks):
            ln_id = f"{ln.ln_id}_chunk_{idx}"
            content_hash = compute_content_hash(chunk_content)

            yield LineageNode(
                ln_id=ln_id,
                content=chunk_content,
                source=ln.source,
                dataset_version=ln.dataset_version,
                transform_chain=ln.transform_chain + [self.name],
                content_hash=content_hash,
                created_at=datetime.utcnow(),
                metadata={**ln.metadata, "chunk_index": idx, "total_chunks": len(chunks)},
            )


class SemanticChunkerTransform(BaseTransform):
    """Transform that applies semantic chunking."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        """Initialize semantic chunker transform."""
        self.chunker = SemanticChunker(chunk_size, overlap)

    @property
    def name(self) -> str:
        """Transform name."""
        return "semantic_chunk"

    def transform(self, ln: LineageNode) -> Iterator[LineageNode]:
        """Chunk a Lineage Node into multiple nodes."""
        chunks = self.chunker.chunk(ln.content)
        for idx, chunk_content in enumerate(chunks):
            ln_id = f"{ln.ln_id}_chunk_{idx}"
            content_hash = compute_content_hash(chunk_content)

            yield LineageNode(
                ln_id=ln_id,
                content=chunk_content,
                source=ln.source,
                dataset_version=ln.dataset_version,
                transform_chain=ln.transform_chain + [self.name],
                content_hash=content_hash,
                created_at=datetime.utcnow(),
                metadata={**ln.metadata, "chunk_index": idx, "total_chunks": len(chunks)},
            )
