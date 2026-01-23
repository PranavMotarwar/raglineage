from typing import Union
"""File-based ingestion (text files, markdown, etc.)."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterator

from raglineage.ingest.base import BaseIngestor
from raglineage.schemas.lineage_node import FileSource, LineageNode
from raglineage.utils.hashing import compute_content_hash
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".text"}


class FileIngestor(BaseIngestor):
    """Ingestor for text files."""

    def __init__(self, dataset_version: str = "v1.0") -> None:
        """
        Initialize file ingestor.

        Args:
            dataset_version: Dataset version tag
        """
        self.dataset_version = dataset_version

    def can_ingest(self, source: Union[Path, str]) -> bool:
        """Check if source is a text file."""
        source = Path(source)
        return source.is_file() and source.suffix.lower() in TEXT_EXTENSIONS

    def ingest(self, source: Union[Path, str]) -> Iterator[LineageNode]:
        """Ingest text file and yield Lineage Nodes."""
        source = Path(source)
        if not self.can_ingest(source):
            return

        try:
            content = source.read_text(encoding="utf-8")
            if not content.strip():
                return

            # Create a single Lineage Node for the file
            ln_id = f"ln_{uuid.uuid4().hex[:8]}"
            content_hash = compute_content_hash(content)

            yield LineageNode(
                ln_id=ln_id,
                content=content,
                source=FileSource(uri=str(source), line_start=1, line_end=None),
                dataset_version=self.dataset_version,
                transform_chain=["file_read"],
                content_hash=content_hash,
                created_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to ingest file {source}: {e}")
