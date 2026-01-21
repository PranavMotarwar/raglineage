"""Tests for incremental update functionality."""

import tempfile
from pathlib import Path

import pytest

from raglineage import RagLineage


def test_incremental_update() -> None:
    """Test incremental update with changed files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "data"
        source_dir.mkdir()

        # Create initial file
        file1 = source_dir / "file1.txt"
        file1.write_text("Initial content")

        # Build initial version
        rag = RagLineage(source=str(source_dir))
        rag.build(version="v1.0")

        # Modify file
        file1.write_text("Modified content")

        # Update to new version
        rag.update(version="v1.1", changed_only=True)

        # Verify version exists
        manifest = rag.version_store.load_manifest()
        assert manifest is not None
        assert manifest.get_version("v1.1") is not None
