"""
Basic raglineage example.

Shows how to:
- Build a database from files
- Query with lineage tracking
- Audit answers

For a full walkthrough, see examples/example/example.py
"""

from pathlib import Path

from raglineage import RagLineage


def main():
    """Run basic raglineage example."""
    # Initialize raglineage with source data directory
    # The examples/data directory contains sample text and CSV files
    source_dir = Path(__file__).parent.parent / "data"
    
    print("Initializing raglineage...")
    rag = RagLineage(
        source=str(source_dir),
        store_backend="faiss",
        embed_backend="local",
        chunk_size=200,  # Smaller chunks for demo
        chunk_overlap=50,
    )
    
    # Build the RAG database (version 1.0)
    print("\nBuilding RAG database from source files...")
    rag.build(version="v1.0")
    print("Build complete!")
    
    # Query the database
    print("\nQuerying: 'What is the refund policy?'")
    answer = rag.query("What is the refund policy?", k=3)
    
    print(f"\nAnswer: {answer.answer}")
    print(f"\nRetrieved {len(answer.lineage)} lineage nodes:")
    
    for i, entry in enumerate(answer.lineage, 1):
        print(f"\n  {i}. Lineage Node: {entry.ln_id[:12]}...")
        print(f"     Score: {entry.score:.3f}")
        print(f"     Source: {entry.source.uri}")
        print(f"     Version: {entry.dataset_version}")
        print(f"     Transforms: {', '.join(entry.transform_chain)}")
    
    # Audit the answer
    print("\n\nAuditing answer...")
    audit_report = rag.audit(answer)
    
    print(f"Staleness Check: {audit_report.staleness_check}")
    print(f"Version Consistency: {audit_report.version_consistency}")
    if audit_report.transform_risk_flags:
        print(f"Risk Flags: {', '.join(audit_report.transform_risk_flags)}")
    else:
        print("Risk Flags: None")
    
    # Show JSON output
    print("\n\nComplete answer with lineage (JSON):")
    print(answer.model_dump_json(indent=2))
    
    print("\n\nAudit report (JSON):")
    print(audit_report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
