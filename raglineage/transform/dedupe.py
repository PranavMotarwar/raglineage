"""Deduplication transform using content hashes."""

from typing import Iterator

from raglineage.schemas.lineage_node import LineageNode
from raglineage.transform.base import BaseTransform
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class DedupeTransform(BaseTransform):
    """Deduplication transform that filters duplicate content."""

    def __init__(self) -> None:
        """Initialize dedupe transform."""
        self.seen_hashes: set[str] = set()

    @property
    def name(self) -> str:
        """Transform name."""
        return "deduplicate"

    def transform(self, ln: LineageNode) -> Iterator[LineageNode]:
        """Filter out duplicate nodes based on content hash."""
        if ln.content_hash in self.seen_hashes:
            logger.debug(f"Skipping duplicate: {ln.ln_id}")
            return

        self.seen_hashes.add(ln.content_hash)
        yield LineageNode(
            ln_id=ln.ln_id,
            content=ln.content,
            source=ln.source,
            dataset_version=ln.dataset_version,
            transform_chain=ln.transform_chain + [self.name],
            content_hash=ln.content_hash,
            created_at=ln.created_at,
            updated_at=ln.updated_at,
            metadata=ln.metadata,
        )

    def reset(self) -> None:
        """Reset seen hashes (useful for new dataset versions)."""
        self.seen_hashes.clear()
