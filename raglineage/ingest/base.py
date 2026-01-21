"""Base ingestor interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from raglineage.schemas.lineage_node import LineageNode


class BaseIngestor(ABC):
    """Base interface for data ingestion."""

    @abstractmethod
    def ingest(self, source: Path | str) -> Iterator[LineageNode]:
        """
        Ingest data from source and yield Lineage Nodes.

        Args:
            source: Source path or URI

        Yields:
            LineageNode objects
        """
        pass

    @abstractmethod
    def can_ingest(self, source: Path | str) -> bool:
        """
        Check if this ingestor can handle the source.

        Args:
            source: Source path or URI

        Returns:
            True if can ingest, False otherwise
        """
        pass
