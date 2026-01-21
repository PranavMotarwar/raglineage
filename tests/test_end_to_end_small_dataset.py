"""End-to-end test with small dataset."""

import tempfile
from pathlib import Path

import pytest

from raglineage import RagLineage


def test_end_to_end() -> None:
    """Test end-to-end workflow with small dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "data"
        source_dir.mkdir()

        # Create test files
        file1 = source_dir / "policy.txt"
        file1.write_text("Refund Policy: 30 days return window. Contact support for refunds.")

        file2 = source_dir / "products.csv"
        file2.write_text("product_id,name,price\n1,Widget,29.99\n2,Gadget,49.99")

        # Build
        rag = RagLineage(source=str(source_dir), chunk_size=50)
        rag.build(version="v1.0")

        # Query
        answer = rag.query("What is the refund policy?", k=3)
        assert answer.question == "What is the refund policy?"
        assert len(answer.lineage) > 0

        # Audit
        report = rag.audit(answer)
        assert report.staleness_check in ["pass", "warning", "fail"]
        assert report.version_consistency in ["single_version", "mixed_versions", "unknown"]

        # Diff (create new version)
        file1.write_text("Refund Policy: 45 days return window. Contact support for refunds.")
        rag.update(version="v1.1", changed_only=True)

        diff = rag.diff("v1.0", "v1.1")
        assert diff.has_changes()
