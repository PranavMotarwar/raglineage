#!/usr/bin/env python3
"""Quick verification script to test raglineage installation."""

import sys
from pathlib import Path

try:
    from raglineage import RagLineage
    from raglineage.schemas.lineage_node import LineageNode, FileSource
    from raglineage.lineage.graph import LineageGraph
    print("✓ raglineage imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test basic functionality
try:
    # Test schema
    source = FileSource(uri="test.txt")
    ln = LineageNode(
        ln_id="ln_test",
        content="Test",
        source=source,
        dataset_version="v1.0",
        transform_chain=[],
        content_hash="sha256:test",
    )
    print("✓ LineageNode creation successful")

    # Test graph
    graph = LineageGraph()
    graph.add_node(ln)
    print("✓ LineageGraph operations successful")

    print("\n✅ All basic functionality verified!")
    print("\nTo test with actual data:")
    print("  python -m pytest tests/")
    print("\nTo run CLI:")
    print("  raglineage --help")

except Exception as e:
    print(f"✗ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
