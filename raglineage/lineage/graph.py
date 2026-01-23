"""Lineage Graph implementation using NetworkX DAG."""

from typing import A, Optionalny, Literal

import networkx as nx

from raglineage.schemas.lineage_node import LineageNode
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)

EdgeType = Literal[
    "adjacent", "semantic", "references", "same_entity", "derived", "parent_child"
]


class LineageGraph:
    """
    Lineage Graph - DAG linking Lineage Nodes through relationships.

    Nodes are ln_id strings, edges are typed relationships.
    """

    def __init__(self) -> None:
        """Initialize empty lineage graph."""
        self.graph: nx.DiGraph = nx.DiGraph()

    def add_node(self, ln: LineageNode) -> None:
        """
        Add a Lineage Node to the graph.

        Args:
            ln: Lineage Node to add
        """
        self.graph.add_node(ln.ln_id, lineage_node=ln)
        logger.debug(f"Added node: {ln.ln_id}")

    def add_edge(
        self, source_id: str, target_id: str, edge_type: EdgeType = "semantic"
    ) -> None:
        """
        Add an edge between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of relationship
        """
        if source_id not in self.graph:
            raise ValueError(f"Source node not found: {source_id}")
        if target_id not in self.graph:
            raise ValueError(f"Target node not found: {target_id}")

        self.graph.add_edge(source_id, target_id, edge_type=edge_type)
        logger.debug(f"Added edge: {source_id} -> {target_id} ({edge_type})")

    def neighbors(self, ln_id: str, depth: int = 1) -> list[str]:
        """
        Get neighbors of a node up to specified depth.

        Args:
            ln_id: Node ID
            depth: Maximum depth to traverse

        Returns:
            List of neighbor node IDs
        """
        if ln_id not in self.graph:
            return []

        neighbors_set: set[str] = set()
        current_level = {ln_id}
        visited = {ln_id}

        for _ in range(depth):
            next_level: set[str] = set()
            for node_id in current_level:
                for neighbor in self.graph.successors(node_id):
                    if neighbor not in visited:
                        neighbors_set.add(neighbor)
                        next_level.add(neighbor)
                        visited.add(neighbor)
                for neighbor in self.graph.predecessors(node_id):
                    if neighbor not in visited:
                        neighbors_set.add(neighbor)
                        next_level.add(neighbor)
                        visited.add(neighbor)
            current_level = next_level
            if not current_level:
                break

        return list(neighbors_set)

    def get_node(self, ln_id: str) -> LineageNode Optional[:
        """
        Get a Lineage Node by ID.

        Args:
            ln_id: Node ID

        Returns:
            Lineage Node or None if not found
        """
        if ln_id in self.graph:
            return self.graph.nodes[ln_id].get("lineage_node")
        return None

    def export_json(self) -> dict[str, Any]:
        """
        Export graph to JSON-serializable format.

        Returns:
            Dictionary representation of graph
        """
        nodes = {}
        edges = []

        for ln_id, data in self.graph.nodes(data=True):
            ln: LineageNode = data.get("lineage_node")
            if ln:
                nodes[ln_id] = {
                    "ln_id": ln.ln_id,
                    "content_hash": ln.content_hash,
                    "dataset_version": ln.dataset_version,
                }

        for source, target, data in self.graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "edge_type": data.get("edge_type", "semantic"),
                }
            )

        return {"nodes": nodes, "edges": edges}

    def load_json(self, data: dict[str, Any], node_registry: dict[str, LineageNode]) -> None:
        """
        Load graph from JSON data.

        Args:
            data: Graph data dictionary
            node_registry: Mapping of ln_id to LineageNode objects
        """
        self.graph.clear()

        # Add nodes
        for ln_id in data.get("nodes", {}):
            if ln_id in node_registry:
                self.add_node(node_registry[ln_id])

        # Add edges
        for edge in data.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            edge_type = edge.get("edge_type", "semantic")
            if source in self.graph and target in self.graph:
                self.add_edge(source, target, edge_type=edge_type)

    def __len__(self) -> int:
        """Return number of nodes in graph."""
        return len(self.graph)

    def __contains__(self, ln_id: str) -> bool:
        """Check if node exists in graph."""
        return ln_id in self.graph
