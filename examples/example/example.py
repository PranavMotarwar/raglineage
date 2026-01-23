"""
Example showing how to use raglineage in practice.

This walks through the main features:
- Building a versioned RAG database
- Querying with full lineage tracking
- Auditing answers for quality
- Incremental updates when data changes
- Comparing versions
- Exploring graph relationships
- Filtering results
"""

from pathlib import Path

from raglineage import RagLineage
from raglineage.retrieval.filters import FilterConfig


def main():
    """Run the raglineage example."""
    print("=" * 70)
    print("raglineage Example")
    print("=" * 70)
    
    # Point to our sample data
    source_dir = Path(__file__).parent.parent / "data"
    print(f"\nUsing data from: {source_dir}")
    
    # Set up raglineage
    print("\n" + "=" * 70)
    print("Setting up raglineage")
    print("=" * 70)
    
    rag = RagLineage(
        source=str(source_dir),
        store_backend="faiss",
        embed_backend="local",
        chunk_size=300,
        chunk_overlap=50,
        chunking_strategy="semantic",
        enable_dedupe=True,
        enable_normalize=True,
        normalize_aggressive=False,
        graph_depth=1,
    )
    
    print("Using FAISS for vector storage and local embeddings")
    
    # Build the database
    print("\n" + "=" * 70)
    print("Building RAG database (v1.0)")
    print("=" * 70)
    
    print("Processing source files...")
    rag.build(version="v1.0")
    
    print(f"\nDone! Created {len(rag.node_registry)} lineage nodes")
    
    # Query the database
    print("\n" + "=" * 70)
    print("Querying the database")
    print("=" * 70)
    
    query = "What is the refund policy?"
    print(f"\nAsking: '{query}'")
    
    answer = rag.query(query, k=5)
    
    print(f"\nAnswer: {answer.answer[:200]}...")
    print(f"\nFound {len(answer.lineage)} relevant chunks:")
    
    for i, entry in enumerate(answer.lineage, 1):
        print(f"\n  {i}. {entry.ln_id}")
        print(f"     Score: {entry.score:.3f}")
        print(f"     From: {entry.source.uri}")
        if hasattr(entry.source, 'page'):
            print(f"     Page: {entry.source.page}")
        if hasattr(entry.source, 'row'):
            print(f"     Row: {entry.source.row}")
        print(f"     Version: {entry.dataset_version}")
        print(f"     Transforms: {' -> '.join(entry.transform_chain)}")
    
    # Check answer quality
    print("\n" + "=" * 70)
    print("Auditing the answer")
    print("=" * 70)
    
    audit_report = rag.audit(answer)
    
    print(f"\nStaleness: {audit_report.staleness_check}")
    print(f"Version consistency: {audit_report.version_consistency}")
    if audit_report.transform_risk_flags:
        print(f"Risks: {', '.join(audit_report.transform_risk_flags)}")
    else:
        print("No risk flags")
    
    # Show the full JSON output
    print("\n" + "=" * 70)
    print("Full lineage JSON")
    print("=" * 70)
    
    print("\nAnswer with lineage:")
    print(answer.model_dump_json(indent=2))
    
    print("\n\nAudit report:")
    print(audit_report.model_dump_json(indent=2))
    
    # Update when files change
    print("\n" + "=" * 70)
    print("Updating incrementally (v1.1)")
    print("=" * 70)
    
    print("\nUpdating database (only processing changed files)...")
    rag.update(version="v1.1", changed_only=True)
    
    print("Done! Only changed files were reprocessed")
    
    # See what changed between versions
    print("\n" + "=" * 70)
    print("Comparing versions")
    print("=" * 70)
    
    print("\nWhat changed between v1.0 and v1.1?")
    diff = rag.diff("v1.0", "v1.1")
    
    if diff.added_files:
        print(f"\nAdded ({len(diff.added_files)}):")
        for f in diff.added_files:
            print(f"  + {f}")
    
    if diff.removed_files:
        print(f"\nRemoved ({len(diff.removed_files)}):")
        for f in diff.removed_files:
            print(f"  - {f}")
    
    if diff.modified_files:
        print(f"\nModified ({len(diff.modified_files)}):")
        for f in diff.modified_files:
            print(f"  ~ {f}")
    
    if not any([diff.added_files, diff.removed_files, diff.modified_files]):
        print("No changes detected")
    
    # Filter results
    print("\n" + "=" * 70)
    print("Filtered query")
    print("=" * 70)
    
    print("\nOnly getting results from v1.0...")
    filters = FilterConfig(
        dataset_version="v1.0",
        min_score=0.5,
    )
    
    filtered_answer = rag.query("refund policy", k=3, filters=filters)
    print(f"Found {len(filtered_answer.lineage)} results (all from v1.0)")
    
    # Explore graph connections
    print("\n" + "=" * 70)
    print("Graph relationships")
    print("=" * 70)
    
    if answer.lineage:
        first_ln_id = answer.lineage[0].ln_id
        print(f"\nLooking at connections from {first_ln_id}...")
        
        neighbors = rag.graph.neighbors(first_ln_id, depth=1)
        print(f"Found {len(neighbors)} connected nodes")
        if neighbors:
            for neighbor_id in neighbors[:5]:
                print(f"  • {neighbor_id}")
    
    # Export the graph
    print("\n" + "=" * 70)
    print("Exporting graph")
    print("=" * 70)
    
    graph_json = rag.graph.export_json()
    print(f"\nExported {len(graph_json.get('nodes', {}))} nodes and {len(graph_json.get('edges', []))} edges")
    
    # Check version history
    print("\n" + "=" * 70)
    print("Version history")
    print("=" * 70)
    
    manifest = rag.version_store.load_manifest()
    if manifest:
        print(f"\nDataset: {manifest.dataset_name}")
        print(f"Current: {manifest.current_version}")
        print(f"Total versions: {len(manifest.versions)}")
        
        for version in manifest.versions:
            print(f"  {version.version} - {len(version.files)} files")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
