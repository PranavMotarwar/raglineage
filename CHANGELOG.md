# Changelog

All notable changes to raglineage will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-20

### Added
- Initial release of raglineage
- Lineage Node (LN) schema with complete provenance tracking
- Lineage Graph (DAG) implementation using NetworkX
- Dataset versioning and manifest management
- Version diffing between dataset versions
- Incremental update support (only recompute changed files)
- Multiple ingestion backends (file, tabular, auto-detection)
- Transform pipeline (chunking, deduplication, normalization)
- FAISS vector store with LN ID mapping
- Local and OpenAI embedding backends
- Retrieval with graph-walk expansion
- Answer auditing with lineage reconstruction
- Version consistency and staleness checks
- CLI interface with typer
- Comprehensive test suite
- Example datasets
- Full documentation

### Features
- **Lineage Tracking**: Every retrievable chunk has immutable ID, source reference, transform chain, content hash, and timestamps
- **Dataset Versioning**: Track dataset versions with file-level change detection
- **Incremental Updates**: Only recompute embeddings for changed files
- **Answer Auditing**: Reconstruct complete provenance of any answer
- **Graph Relationships**: DAG linking nodes through semantic and structural relationships
- **Multiple Formats**: Support for text files, CSV, JSON
- **Production Ready**: Persistent storage, error handling, logging

### Technical Details
- Python ≥ 3.10
- Built with Pydantic for schemas
- NetworkX for graph operations
- FAISS for vector storage
- Sentence-transformers for embeddings
- Type hints throughout
- Comprehensive test coverage
