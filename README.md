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
- Precise source reference (file path, page, row, URL, etc.)
- Full transform chain (ordered list of transforms applied)
- Content hash for integrity
- Timestamps for auditing

The system maintains a **Lineage Graph (DAG)** linking nodes through structural and semantic relationships, enabling:

- Dataset versioning and diffing
- Incremental rebuilds (only recompute what changed)
- Answer auditing (reconstruct provenance of any answer)
- Version consistency checks
- Staleness detection

This is **not** a LangChain/LlamaIndex wrapper—it's a first-class lineage system.

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

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache-2.0 License. See [LICENSE](LICENSE) for details.

## Author

Pranav Motarwar - [GitHub](https://github.com/PranavMotarwar)

---

**raglineage** - Where every answer has a traceable origin.
