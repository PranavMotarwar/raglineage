"""
Comprehensive example demonstrating all raglineage functionalities.

This example covers:
1. Building a RAG database with versioning
2. Querying with lineage tracking
3. Answer auditing
4. Incremental updates
5. Version diffing
6. Graph relationships
7. Filtering and advanced retrieval
8. Exporting lineage data
"""

from pathlib import Path

from raglineage import RagLineage
from raglineage.retrieval.filters import FilterConfig


def main():
    """Demonstrate all raglineage features."""
    print("=" * 70)
    print("raglineage Comprehensive Example")
    print("=" * 70)
    
    # Setup
    source_dir = Path(__file__).parent.parent / "data"
    print(f"\nSource directory: {source_dir}")
    
    # Initialize raglineage
    print("\n" + "=" * 70)
    print("1. INITIALIZING RAGLINEAGE")
    print("=" * 70)
    
    rag = RagLineage(
        source=str(source_dir),
        store_backend="faiss",
        embed_backend="local",
        chunk_size=300,  # Smaller chunks for demo
        chunk_overlap=50,
        chunking_strategy="semantic",  # Use semantic chunking
        enable_dedupe=True,
        enable_normalize=True,
        normalize_aggressive=False,
        graph_depth=1,  # Graph walk depth for retrieval
    )
    
    print("Configuration:")
    print(f"  - Store backend: FAISS")
    print(f"  - Embed backend: Local (sentence-transformers)")
    print(f"  - Chunk size: 300")
    print(f"  - Chunking strategy: Semantic")
    print(f"  - Deduplication: Enabled")
    print(f"  - Normalization: Enabled")
    
    # Build initial version
    print("\n" + "=" * 70)
    print("2. BUILDING RAG DATABASE (Version v1.0)")
    print("=" * 70)
    
    print("Building from source files...")
    rag.build(version="v1.0")
    
    print("\nBuild complete! Database includes:")
    print(f"  - Lineage nodes: {len(rag.node_registry)}")
    print(f"  - Graph nodes: {len(rag.graph)}")
    print(f"  - Vector store entries: {len(rag.store) if rag.store else 0}")
    
    # Query with lineage
    print("\n" + "=" * 70)
    print("3. QUERYING WITH LINEAGE TRACKING")
    print("=" * 70)
    
    query = "What is the refund policy?"
    print(f"\nQuery: '{query}'")
    
    answer = rag.query(query, k=5)
    
    print(f"\nAnswer: {answer.answer[:200]}...")
    print(f"\nRetrieved {len(answer.lineage)} lineage nodes:")
    
    for i, entry in enumerate(answer.lineage, 1):
        print(f"\n  {i}. Lineage Node ID: {entry.ln_id}")
        print(f"     Similarity Score: {entry.score:.3f}")
        print(f"     Source: {entry.source.uri}")
        if hasattr(entry.source, 'page'):
            print(f"     Page: {entry.source.page}")
        if hasattr(entry.source, 'row'):
            print(f"     Row: {entry.source.row}")
        print(f"     Dataset Version: {entry.dataset_version}")
        print(f"     Transform Chain: {' -> '.join(entry.transform_chain)}")
    
    # Answer auditing
    print("\n" + "=" * 70)
    print("4. ANSWER AUDITING")
    print("=" * 70)
    
    audit_report = rag.audit(answer)
    
    print("\nAudit Report:")
    print(f"  - Staleness Check: {audit_report.staleness_check}")
    print(f"  - Version Consistency: {audit_report.version_consistency}")
    if audit_report.transform_risk_flags:
        print(f"  - Risk Flags: {', '.join(audit_report.transform_risk_flags)}")
    else:
        print(f"  - Risk Flags: None (all transforms are safe)")
    
    # Show complete JSON output
    print("\n" + "=" * 70)
    print("5. COMPLETE LINEAGE JSON OUTPUT")
    print("=" * 70)
    
    print("\nAnswer with Lineage (JSON):")
    print(answer.model_dump_json(indent=2))
    
    print("\n\nAudit Report (JSON):")
    print(audit_report.model_dump_json(indent=2))
    
    # Incremental update
    print("\n" + "=" * 70)
    print("6. INCREMENTAL UPDATE (Version v1.1)")
    print("=" * 70)
    
    print("\nSimulating file update...")
    # In a real scenario, you would modify files here
    # For demo, we'll just show the update process
    
    print("Updating database incrementally (only changed files)...")
    rag.update(version="v1.1", changed_only=True)
    
    print("\nUpdate complete!")
    print("  - Only changed files were reprocessed")
    print("  - Embeddings recomputed only for modified content")
    print("  - Graph updated incrementally")
    
    # Version diffing
    print("\n" + "=" * 70)
    print("7. VERSION DIFFING")
    print("=" * 70)
    
    print("\nComparing versions v1.0 and v1.1...")
    diff = rag.diff("v1.0", "v1.1")
    
    print(f"\nDiff Results:")
    print(f"  - Added files: {len(diff.added_files)}")
    if diff.added_files:
        for f in diff.added_files:
            print(f"    + {f}")
    
    print(f"  - Removed files: {len(diff.removed_files)}")
    if diff.removed_files:
        for f in diff.removed_files:
            print(f"    - {f}")
    
    print(f"  - Modified files: {len(diff.modified_files)}")
    if diff.modified_files:
        for f in diff.modified_files:
            print(f"    ~ {f}")
    
    print(f"  - Unchanged files: {len(diff.unchanged_files)}")
    
    # Filtered query
    print("\n" + "=" * 70)
    print("8. FILTERED QUERY")
    print("=" * 70)
    
    print("\nQuerying with filters (version-specific)...")
    filters = FilterConfig(
        dataset_version="v1.0",  # Only get results from v1.0
        min_score=0.5,  # Minimum similarity score
    )
    
    filtered_answer = rag.query("refund policy", k=3, filters=filters)
    print(f"\nFiltered results: {len(filtered_answer.lineage)} nodes")
    print("All results are from version v1.0")
    
    # Graph relationships
    print("\n" + "=" * 70)
    print("9. GRAPH RELATIONSHIPS")
    print("=" * 70)
    
    if answer.lineage:
        first_ln_id = answer.lineage[0].ln_id
        print(f"\nExploring graph from node: {first_ln_id}")
        
        neighbors = rag.graph.neighbors(first_ln_id, depth=1)
        print(f"  - Direct neighbors: {len(neighbors)}")
        if neighbors:
            print("  - Neighbor IDs:")
            for neighbor_id in neighbors[:5]:  # Show first 5
                print(f"    • {neighbor_id}")
        
        # Get node from graph
        node = rag.graph.get_node(first_ln_id)
        if node:
            print(f"\n  - Node content preview: {node.content[:100]}...")
            print(f"  - Node transform chain: {' -> '.join(node.transform_chain)}")
    
    # Export lineage graph
    print("\n" + "=" * 70)
    print("10. EXPORTING LINEAGE GRAPH")
    print("=" * 70)
    
    graph_json = rag.graph.export_json()
    print(f"\nGraph exported:")
    print(f"  - Nodes: {len(graph_json.get('nodes', {}))}")
    print(f"  - Edges: {len(graph_json.get('edges', []))}")
    print(f"  - Edge types: {set(e.get('edge_type') for e in graph_json.get('edges', []))}")
    
    # Dataset versioning info
    print("\n" + "=" * 70)
    print("11. DATASET VERSIONING INFORMATION")
    print("=" * 70)
    
    manifest = rag.version_store.load_manifest()
    if manifest:
        print(f"\nDataset: {manifest.dataset_name}")
        print(f"Current version: {manifest.current_version}")
        print(f"Total versions: {len(manifest.versions)}")
        
        print("\nVersion history:")
        for version in manifest.versions:
            print(f"  - {version.version} ({len(version.files)} files)")
            print(f"    Created: {version.created_at}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\nraglineage provides:")
    print("  ✓ Complete lineage tracking for every chunk")
    print("  ✓ Dataset versioning with file-level change detection")
    print("  ✓ Incremental updates (only recompute changed files)")
    print("  ✓ Answer auditing with provenance reconstruction")
    print("  ✓ Graph-based relationships between chunks")
    print("  ✓ Version diffing and comparison")
    print("  ✓ Filtered retrieval by version, source, type")
    print("  ✓ Export lineage data as JSON")
    print("  ✓ Persistent storage with FAISS")
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
