"""Retriever for querying with graph expansion."""

from typing import Optional

import numpy as np

from raglineage.embedding.base import BaseEmbedder
from raglineage.lineage.graph import LineageGraph
from raglineage.retrieval.filters import FilterConfig, apply_filters
from raglineage.schemas.lineage_node import LineageNode
from raglineage.store.base import BaseVectorStore
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class Retriever:
    """Retriever with graph-walk expansion."""

    def __init__(
        self,
        embedder: BaseEmbedder,
        store: BaseVectorStore,
        graph: LineageGraph,
        node_registry: dict[str, LineageNode],
    ) -> None:
        """
        Initialize retriever.

        Args:
            embedder: Embedding model
            store: Vector store
            graph: Lineage graph
            node_registry: Dictionary of ln_id -> LineageNode
        """
        self.embedder = embedder
        self.store = store
        self.graph = graph
        self.node_registry = node_registry

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filters: Optional[FilterConfig] = None,
        graph_depth: int = 0,
    ) -> list[tuple[str, float]]:
        """
        Retrieve similar nodes with optional graph expansion.

        Args:
            query: Query text
            k: Number of results to return
            filters: Optional filter configuration
            graph_depth: Depth for graph walk expansion (0 = no expansion)

        Returns:
            List of (ln_id, score) tuples
        """
        if not query.strip():
            raise ValueError("query must not be empty")
        if k <= 0:
            raise ValueError("k must be greater than zero")

        # Embed query
        query_embedding = self.embedder.embed(query)

        # Vector search
        results = self.store.search(query_embedding, k=k * 2)  # Get more for filtering

        # Graph expansion
        if graph_depth > 0:
            expanded_results = dict(results)
            for ln_id, _ in results:
                neighbors = self.graph.neighbors(ln_id, depth=graph_depth)
                for neighbor_id in neighbors:
                    if neighbor_id in self.node_registry:
                        expanded_results.setdefault(neighbor_id, 0.8)

            results = list(expanded_results.items())

        # Apply filters after graph expansion so neighbors cannot bypass them.
        if filters:
            results = apply_filters(results, self.node_registry, filters)

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:k]
