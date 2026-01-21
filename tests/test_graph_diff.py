"""Tests for graph and diff functionality."""

from datetime import datetime

import pytest

from raglineage.lineage.diff import compute_diff
from raglineage.lineage.graph import LineageGraph
from raglineage.schemas.dataset import DatasetVersion, FileEntry
from raglineage.schemas.lineage_node import FileSource, LineageNode


def test_graph_add_node() -> None:
    """Test adding nodes to graph."""
    graph = LineageGraph()
    source = FileSource(uri="test.txt")
    ln = LineageNode(
        ln_id="ln_1",
        content="Test",
        source=source,
        dataset_version="v1.0",
        transform_chain=[],
        content_hash="sha256:test",
    )

    graph.add_node(ln)
    assert "ln_1" in graph
    assert len(graph) == 1


def test_graph_add_edge() -> None:
    """Test adding edges to graph."""
    graph = LineageGraph()
    source = FileSource(uri="test.txt")

    ln1 = LineageNode(
        ln_id="ln_1",
        content="Test 1",
        source=source,
        dataset_version="v1.0",
        transform_chain=[],
        content_hash="sha256:test1",
    )
    ln2 = LineageNode(
        ln_id="ln_2",
        content="Test 2",
        source=source,
        dataset_version="v1.0",
        transform_chain=[],
        content_hash="sha256:test2",
    )

    graph.add_node(ln1)
    graph.add_node(ln2)
    graph.add_edge("ln_1", "ln_2", edge_type="adjacent")

    neighbors = graph.neighbors("ln_1", depth=1)
    assert "ln_2" in neighbors


def test_version_diff() -> None:
    """Test version diffing."""
    version_from = DatasetVersion(
        version="v1.0",
        created_at=datetime.utcnow(),
        files=[
            FileEntry(path="file1.txt", hash="hash1", size=100, modified_at=datetime.utcnow()),
            FileEntry(path="file2.txt", hash="hash2", size=200, modified_at=datetime.utcnow()),
        ],
    )

    version_to = DatasetVersion(
        version="v1.1",
        created_at=datetime.utcnow(),
        files=[
            FileEntry(path="file1.txt", hash="hash1_modified", size=150, modified_at=datetime.utcnow()),
            FileEntry(path="file2.txt", hash="hash2", size=200, modified_at=datetime.utcnow()),
            FileEntry(path="file3.txt", hash="hash3", size=300, modified_at=datetime.utcnow()),
        ],
    )

    diff = compute_diff(version_from, version_to)

    assert "file1.txt" in diff.modified_files
    assert "file3.txt" in diff.added_files
    assert "file2.txt" in diff.unchanged_files
    assert diff.has_changes()
