"""Tests for LineageNode schema."""

from datetime import datetime

import pytest

from raglineage.schemas.lineage_node import FileSource, LineageNode


def test_lineage_node_creation() -> None:
    """Test creating a LineageNode."""
    source = FileSource(uri="test.txt", line_start=1, line_end=10)
    ln = LineageNode(
        ln_id="ln_test",
        content="Test content",
        source=source,
        dataset_version="v1.0",
        transform_chain=["file_read"],
        content_hash="sha256:test",
    )

    assert ln.ln_id == "ln_test"
    assert ln.content == "Test content"
    assert ln.dataset_version == "v1.0"
    assert ln.transform_chain == ["file_read"]
    assert ln.content_hash == "sha256:test"


def test_lineage_node_json_serialization() -> None:
    """Test JSON serialization."""
    source = FileSource(uri="test.txt")
    ln = LineageNode(
        ln_id="ln_test",
        content="Test",
        source=source,
        dataset_version="v1.0",
        transform_chain=[],
        content_hash="sha256:test",
    )

    json_str = ln.model_dump_json()
    assert "ln_test" in json_str
    assert "Test" in json_str
