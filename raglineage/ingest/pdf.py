"""Optional text-based PDF ingestion with physical page provenance."""

import hashlib
from collections.abc import Iterator
from pathlib import Path

from raglineage.ingest.base import BaseIngestor
from raglineage.schemas.lineage_node import LineageNode, PDFSource
from raglineage.utils.hashing import compute_content_hash
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class PDFIngestor(BaseIngestor):
    """Extract one node per non-empty page; no OCR or password support."""

    def __init__(self, dataset_version: str = "v1.0") -> None:
        self.dataset_version = dataset_version

    def can_ingest(self, source: Path | str) -> bool:
        """Recognize PDFs without importing the optional parser."""
        source = Path(source)
        return source.is_file() and source.suffix.lower() == ".pdf"

    def ingest(self, source: Path | str) -> Iterator[LineageNode]:
        """Yield page nodes with stable IDs and one-based physical page numbers.

        Raises ImportError when the PDF extra is missing and ValueError for
        encrypted or unreadable PDFs. Empty pages are skipped with a warning.
        """
        source = Path(source)
        if not self.can_ingest(source):
            return
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError(
                "PDF ingestion requires pypdf. Install it with: pip install 'raglineage[pdf]'"
            ) from exc

        try:
            with source.open("rb") as stream:
                reader = PdfReader(stream)
                if reader.is_encrypted:
                    raise ValueError("Encrypted PDFs are unsupported; provide a decrypted copy")
                for page_number, page in enumerate(reader.pages, 1):
                    content = page.extract_text() or ""
                    if not content.strip():
                        logger.warning(
                            "PDF %s page %s has no extractable text; skipping. "
                            "It may be blank or scanned; scanned pages require OCR "
                            "before ingestion.", source, page_number,
                        )
                        continue
                    content_hash = compute_content_hash(content)
                    identity = f"{source.resolve()}:{page_number}:{content_hash}".encode()
                    yield LineageNode(
                        ln_id=f"ln_{hashlib.sha256(identity).hexdigest()[:16]}",
                        content=content,
                        source=PDFSource(uri=str(source), page=page_number),
                        dataset_version=self.dataset_version,
                        transform_chain=["pdf_parse"],
                        content_hash=content_hash,
                    )
        except Exception as exc:
            raise ValueError(f"Failed to ingest PDF {source}: {exc}") from exc
