"""Text normalization transform."""

import re
from datetime import datetime
from typing import Iterator

from raglineage.schemas.lineage_node import LineageNode
from raglineage.transform.base import BaseTransform
from raglineage.utils.hashing import compute_content_hash
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class NormalizeTransform(BaseTransform):
    """Text normalization transform (cleanup, whitespace, etc.)."""

    def __init__(self, aggressive: bool = False) -> None:
        """
        Initialize normalize transform.

        Args:
            aggressive: If True, applies aggressive normalization
        """
        self.aggressive = aggressive

    @property
    def name(self) -> str:
        """Transform name."""
        return "normalize_aggressive" if self.aggressive else "normalize"

    def transform(self, ln: LineageNode) -> Iterator[LineageNode]:
        """Normalize text content."""
        content = ln.content

        # Basic normalization
        content = re.sub(r"\s+", " ", content)  # Normalize whitespace
        content = content.strip()

        if self.aggressive:
            # Aggressive normalization
            content = re.sub(r"[^\w\s.,!?;:-]", "", content)  # Remove special chars
            content = content.lower()

        content_hash = compute_content_hash(content)

        yield LineageNode(
            ln_id=ln.ln_id,
            content=content,
            source=ln.source,
            dataset_version=ln.dataset_version,
            transform_chain=ln.transform_chain + [self.name],
            content_hash=content_hash,
            created_at=ln.created_at,
            updated_at=datetime.utcnow(),
            metadata={**ln.metadata, "normalization_aggressive": self.aggressive},
        )
