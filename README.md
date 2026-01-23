# raglineage

**Lineage-aware RAG engine for auditable, reproducible, versioned retrieval and answers**

[![PyPI version](https://badge.fury.io/py/raglineage.svg)](https://badge.fury.io/py/raglineage)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI downloads](https://img.shields.io/pypi/dm/raglineage.svg)](https://pypi.org/project/raglineage/)

## The Unique Idea

Most RAG tools store text chunks and embeddings. They lose provenance and cannot explain answer drift.

**raglineage** treats RAG as a data lineage and provenance problem, not just vector search. Every retrievable unit is a **Lineage Node (LN)** with:

- Immutable ID and dataset version
- Precise source reference (file path, page, row, URL)
- Full transform chain (ordered list of transforms applied)
- Content hash for integrity
- Timestamps for auditing

The system maintains a **Lineage Graph (DAG)** linking nodes through structural and semantic relationships, enabling:

- Dataset versioning and diffing
- Incremental rebuilds (only recompute what changed)
- Answer auditing (reconstruct provenance of any answer)
- Version consistency checks
- Staleness detection

This is **not** a LangChain/LlamaIndex wrapper, rather we wanted a first-class lineage system.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Sources                            │
│  (PDFs, CSVs, JSON, APIs, Text Files)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ingestion Layer                           │
│  AutoIngestor → FileIngestor → TabularIngestor              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Transform Layer                            │
│  Chunkers → Dedupe → Normalize                              │
│  (Each transform recorded in transform_chain)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Lineage Node Creation                           │
│  ln_id, source, transform_chain, content_hash, version      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Lineage Graph (DAG)                             │
│  networkx DAG: nodes=LN, edges=relationships                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Embedding + Vector Store                        │
│  Embeddings → FAISS Store → LN ID Mapping                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Retrieval + Audit                               │
│  Query → Top-K → Graph Walk → Answer + Lineage             │
│  Audit → Version Check → Staleness → Risk Flags             │
└─────────────────────────────────────────────────────────────┘
```

## Lineage Node Example

Every retrievable chunk is a Lineage Node with complete provenance:

```json
{
  "ln_id": "ln_92af",
  "content": "Revenue declined due to supply constraints",
  "source": {
    "type": "pdf",
    "uri": "data/10Q_Q3_2023.pdf",
    "page": 14,
    "section": "Management Discussion"
  },
  "dataset_version": "v3.1",
  "transform_chain": [
    "pdf_parse",
    "section_split",
    "semantic_chunk",
    "deduplicate"
  ],
  "content_hash": "sha256:a3f5b8c9d2e1f4a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
  "created_at": "2026-01-20T00:00:00Z"
}
```

## Audited Answer Example

Every answer includes full lineage and audit metadata:

```json
{
  "question": "Why did revenue fall in Q3?",
  "answer": "Revenue declined primarily due to supply constraints affecting shipments.",
  "lineage": [
    {
      "ln_id": "ln_92af",
      "score": 0.91,
      "source": {
        "uri": "data/10Q_Q3_2023.pdf",
        "page": 14
      },
      "dataset_version": "v3.1",
      "transform_chain": ["pdf_parse","section_split","semantic_chunk","deduplicate"]
    }
  ],
  "audit": {
    "staleness_check": "pass",
    "version_consistency": "single_version",
    "transform_risk_flags": []
  }
}
```

## Quickstart

### Installation

```bash
pip install raglineage
```

### Basic Usage

```python
from raglineage import RagLineage

rag = RagLineage(
    source="examples/data",
    store_backend="faiss",
    embed_backend="local"
)

# Build initial version
rag.build(version="v1.0")

# Query with lineage
ans = rag.query("What is the refund policy?", k=5)
print(ans.model_dump_json(indent=2))

# Audit the answer
report = rag.audit(ans)
print(report.model_dump_json(indent=2))
```

### Examples

Check out the examples directory:
- `examples/example/example.py` - Full walkthrough of all features
- `examples/basic_usage/example.py` - Quick start example

### CLI Usage

```bash
# Initialize a project
raglineage init ./my_project

# Build from source
raglineage build --source ./data --version v1.0

# Update incrementally
raglineage update --source ./data --version v1.1 --changed-only

# Query
raglineage query "What is the refund policy?" --k 5

# Diff versions
raglineage diff v1.0 v1.1
```

## Comparison with Other RAG Tools

| Feature | raglineage | LangChain | LlamaIndex |
|---------|-----------|-----------|------------|
| **Lineage Tracking** | First-class | Not built-in | Not built-in |
| **Dataset Versioning** | Native | Manual | Manual |
| **Incremental Updates** | Automatic | Full rebuild | Full rebuild |
| **Answer Auditing** | Built-in | Manual | Manual |
| **Transform Chain Tracking** | Every LN | Not tracked | Not tracked |
| **Version Diffing** | Structured | Not available | Not available |
| **Graph Relationships** | DAG-based | Optional | Optional |
| **Source Provenance** | Complete | Basic | Basic |

**Key Difference**: raglineage treats lineage as a core requirement, not an afterthought. Every operation preserves and tracks provenance.

## Core Concepts

### Lineage Nodes (LN)

A Lineage Node is the atomic unit of retrieval. Each LN has:
- **ln_id**: Stable, deterministic identifier
- **content**: The actual text content
- **source**: Precise reference to origin (file, page, row, etc.)
- **dataset_version**: Version tag for the dataset
- **transform_chain**: Ordered list of transforms applied
- **content_hash**: SHA-256 hash for integrity
- **timestamps**: Created/updated timestamps

### Lineage Graph

A directed acyclic graph (DAG) where:
- **Nodes**: Lineage Node IDs
- **Edges**: Typed relationships (adjacent, semantic, references, same_entity, etc.)

Enables graph-walk retrieval and relationship exploration.

### Dataset Versioning

Each dataset build produces a versioned manifest:
- Tracks all source files and their hashes
- Enables diffing between versions
- Supports incremental updates (only recompute changed files)

### Answer Auditing

Every answer includes:
- **Lineage**: List of LNs used with scores and metadata
- **Audit Report**: 
  - Version consistency check
  - Staleness detection
  - Transform risk flags

## Complete Feature Set

### 1. Data Ingestion
- **Auto-detection**: Automatically detects file types and routes to appropriate ingestor
- **File Ingestion**: Text files (.txt, .md, .rst)
- **Tabular Ingestion**: CSV, JSON files (row-by-row processing)
- **Extensible**: Easy to add custom ingestors for PDFs, APIs, databases

### 2. Transform Pipeline
- **Chunking Strategies**:
  - Simple chunking (character-based with overlap)
  - Semantic chunking (sentence-aware with overlap)
- **Deduplication**: Content hash-based duplicate detection
- **Normalization**: Text cleanup and normalization (with aggressive mode)
- **Transform Chain Tracking**: Every transform is recorded in the lineage

### 3. Embedding Backends
- **Local Embeddings**: sentence-transformers (default: all-MiniLM-L6-v2)
- **OpenAI Embeddings**: Optional OpenAI API integration
- **Extensible**: Easy to add custom embedding backends

### 4. Vector Storage
- **FAISS Store**: Efficient similarity search with L2 distance
- **LN ID Mapping**: Bidirectional mapping between vector indices and Lineage Node IDs
- **Persistence**: Stores index and mappings to disk
- **Incremental Updates**: Add/update vectors without full rebuild

### 5. Retrieval
- **Top-K Retrieval**: Standard vector similarity search
- **Graph-Walk Expansion**: Expand results using graph relationships
- **Filtering**: Filter by version, source URI, source type, minimum score
- **Configurable Depth**: Control graph walk depth for expansion

### 6. Lineage Graph
- **DAG Structure**: NetworkX-based directed acyclic graph
- **Relationship Types**: adjacent, semantic, references, same_entity, derived, parent_child
- **Graph Operations**:
  - Add nodes and edges
  - Get neighbors at specified depth
  - Export/import as JSON
  - Query node information

### 7. Dataset Versioning
- **Version Manifests**: Track all versions with file lists and hashes
- **File Tracking**: SHA-256 hashes for change detection
- **Version Comparison**: Diff between any two versions
- **Current Version**: Track active version

### 8. Incremental Updates
- **Change Detection**: Automatically detects changed files using hashes
- **Selective Processing**: Only processes added/modified files
- **Efficient Rebuilds**: Recomputes embeddings only for changed content
- **Graph Updates**: Incrementally updates graph relationships

### 9. Answer Auditing
- **Staleness Detection**: Checks if answer uses outdated data
- **Version Consistency**: Verifies all sources are from same version
- **Transform Risk Analysis**: Flags risky transforms (OCR, aggressive normalization, etc.)
- **Complete Audit Reports**: JSON-serializable audit metadata

### 10. CLI Interface
- **raglineage init**: Initialize a new project
- **raglineage build**: Build database from source
- **raglineage update**: Incrementally update database
- **raglineage query**: Query with lineage output
- **raglineage diff**: Compare dataset versions

### 11. Export and Integration
- **JSON Export**: Export lineage graph, answers, audit reports as JSON
- **Python API**: Full programmatic access to all features
- **Type Hints**: Complete type annotations for IDE support
- **Pydantic Models**: All data structures are Pydantic models for validation

## Requirements

- Python ≥ 3.10
- Strict type hints throughout
- Pydantic models for schemas
- NetworkX for graph operations
- FAISS for vector storage
- Sentence-transformers for local embeddings

## Development

```bash
# Clone repository
git clone https://github.com/PranavMotarwar/raglineage.git
cd raglineage
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache-2.0 License. See [LICENSE](LICENSE) for details.

## Author

Pranav Motarwar - [GitHub](https://github.com/PranavMotarwar)

---

**raglineage** - Where every answer has a traceable origin.
