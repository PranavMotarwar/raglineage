"""Auto-detecting ingestor that routes to appropriate ingestor."""

from pathlib import Path
from typing import Iterator

from raglineage.ingest.base import BaseIngestor
from raglineage.ingest.files import FileIngestor
from raglineage.ingest.tabular import TabularIngestor
from raglineage.schemas.lineage_node import LineageNode
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class AutoIngestor(BaseIngestor):
    """Auto-detecting ingestor that selects appropriate ingestor."""

    def __init__(self, dataset_version: str = "v1.0") -> None:
        """
        Initialize auto ingestor.

        Args:
            dataset_version: Dataset version tag
        """
        self.dataset_version = dataset_version
        self.ingestors: list[BaseIngestor] = [
            TabularIngestor(dataset_version),
            FileIngestor(dataset_version),
        ]

    def can_ingest(self, source: Union[Path, str]) -> bool:
        """Check if any ingestor can handle the source."""
        source = Path(source)
        return source.exists() and any(ingestor.can_ingest(source) for ingestor in self.ingestors)

    def ingest(self, source: Union[Path, str]) -> Iterator[LineageNode]:
        """Auto-detect and use appropriate ingestor."""
        source = Path(source)
        if not source.exists():
            logger.warning(f"Source does not exist: {source}")
            return

        for ingestor in self.ingestors:
            if ingestor.can_ingest(source):
                logger.debug(f"Using {ingestor.__class__.__name__} for {source}")
                yield from ingestor.ingest(source)
                return

        logger.warning(f"No ingestor found for: {source}")
