"""Filtering for retrieval results."""

from typing import Any

from raglineage.schemas.lineage_node import LineageNode
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class FilterConfig:
    """Configuration for retrieval filters."""

    def __init__(
        self,
        dataset_version: str | None = None,
        source_uri: str | None = None,
        source_type: str | None = None,
        min_score: float = 0.0,
    ) -> None:
        """
        Initialize filter configuration.

        Args:
            dataset_version: Filter by dataset version
            source_uri: Filter by source URI
            source_type: Filter by source type
            min_score: Minimum similarity score
        """
        self.dataset_version = dataset_version
        self.source_uri = source_uri
        self.source_type = source_type
        self.min_score = min_score


def apply_filters(
    results: list[tuple[str, float]], nodes: dict[str, LineageNode], filters: FilterConfig
) -> list[tuple[str, float]]:
    """
    Apply filters to retrieval results.

    Args:
        results: List of (ln_id, score) tuples
        nodes: Dictionary of ln_id -> LineageNode
        filters: Filter configuration

    Returns:
        Filtered list of (ln_id, score) tuples
    """
    filtered = []
    for ln_id, score in results:
        if score < filters.min_score:
            continue

        if ln_id not in nodes:
            continue

        ln = nodes[ln_id]

        # Version filter
        if filters.dataset_version and ln.dataset_version != filters.dataset_version:
            continue

        # Source URI filter
        if filters.source_uri and ln.source.uri != filters.source_uri:
            continue

        # Source type filter
        if filters.source_type and ln.source.type != filters.source_type:
            continue

        filtered.append((ln_id, score))

    return filtered
