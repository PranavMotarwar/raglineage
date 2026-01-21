"""Base transform interface."""

from abc import ABC, abstractmethod
from typing import Iterator

from raglineage.schemas.lineage_node import LineageNode


class BaseTransform(ABC):
    """Base interface for transforms."""

    @abstractmethod
    def transform(self, ln: LineageNode) -> Iterator[LineageNode]:
        """
        Transform a Lineage Node, yielding zero or more new nodes.

        Args:
            ln: Input Lineage Node

        Yields:
            Transformed Lineage Node(s)
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return transform name (used in transform_chain)."""
        pass
