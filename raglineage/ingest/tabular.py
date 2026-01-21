"""Tabular data ingestion (CSV, JSON, Parquet)."""

import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from raglineage.ingest.base import BaseIngestor
from raglineage.schemas.lineage_node import LineageNode, TabularSource
from raglineage.utils.hashing import compute_content_hash
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class TabularIngestor(BaseIngestor):
    """Ingestor for tabular data (CSV, JSON)."""

    def __init__(self, dataset_version: str = "v1.0") -> None:
        """
        Initialize tabular ingestor.

        Args:
            dataset_version: Dataset version tag
        """
        self.dataset_version = dataset_version

    def can_ingest(self, source: Path | str) -> bool:
        """Check if source is a tabular file."""
        source = Path(source)
        return source.is_file() and source.suffix.lower() in {".csv", ".json", ".parquet"}

    def ingest(self, source: Path | str) -> Iterator[LineageNode]:
        """Ingest tabular file and yield Lineage Nodes (one per row)."""
        source = Path(source)
        if not self.can_ingest(source):
            return

        try:
            if source.suffix.lower() == ".csv":
                yield from self._ingest_csv(source)
            elif source.suffix.lower() == ".json":
                yield from self._ingest_json(source)
            else:
                logger.warning(f"Unsupported tabular format: {source.suffix}")
        except Exception as e:
            logger.error(f"Failed to ingest tabular file {source}: {e}")

    def _ingest_csv(self, source: Path) -> Iterator[LineageNode]:
        """Ingest CSV file."""
        with source.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader):
                content = json.dumps(row, ensure_ascii=False)
                ln_id = f"ln_{uuid.uuid4().hex[:8]}"
                content_hash = compute_content_hash(content)

                yield LineageNode(
                    ln_id=ln_id,
                    content=content,
                    source=TabularSource(uri=str(source), row=row_idx, column=None),
                    dataset_version=self.dataset_version,
                    transform_chain=["csv_parse"],
                    content_hash=content_hash,
                    created_at=datetime.utcnow(),
                )

    def _ingest_json(self, source: Path) -> Iterator[LineageNode]:
        """Ingest JSON file (array of objects)."""
        with source.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for row_idx, item in enumerate(data):
                    content = json.dumps(item, ensure_ascii=False)
                    ln_id = f"ln_{uuid.uuid4().hex[:8]}"
                    content_hash = compute_content_hash(content)

                    yield LineageNode(
                        ln_id=ln_id,
                        content=content,
                        source=TabularSource(uri=str(source), row=row_idx, column=None),
                        dataset_version=self.dataset_version,
                        transform_chain=["json_parse"],
                        content_hash=content_hash,
                        created_at=datetime.utcnow(),
                    )
            else:
                # Single object
                content = json.dumps(data, ensure_ascii=False)
                ln_id = f"ln_{uuid.uuid4().hex[:8]}"
                content_hash = compute_content_hash(content)

                yield LineageNode(
                    ln_id=ln_id,
                    content=content,
                    source=TabularSource(uri=str(source), row=0, column=None),
                    dataset_version=self.dataset_version,
                    transform_chain=["json_parse"],
                    content_hash=content_hash,
                    created_at=datetime.utcnow(),
                )
