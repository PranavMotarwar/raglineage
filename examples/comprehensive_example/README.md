# Comprehensive raglineage Example

This example demonstrates all major features of raglineage.

## Features Demonstrated

### 1. Initialization and Configuration
- Setting up raglineage with custom parameters
- Configuring chunking strategy (semantic vs simple)
- Enabling/disabling transforms (deduplication, normalization)
- Setting graph walk depth for retrieval

### 2. Building RAG Database
- Building from source files (text, CSV, JSON)
- Creating versioned dataset (v1.0)
- Automatic lineage node creation
- Graph construction with relationships

### 3. Querying with Lineage
- Querying the database
- Retrieving top-k results with similarity scores
- Complete lineage information for each result:
  - Lineage Node ID
  - Source reference (file, page, row)
  - Dataset version
  - Transform chain (all operations applied)
  - Content hash

### 4. Answer Auditing
- Staleness detection (checking if answer is outdated)
- Version consistency checking (single vs mixed versions)
- Transform risk flag detection
- Complete audit report generation

### 5. Incremental Updates
- Updating database with new version (v1.1)
- Only processing changed files (changed_only=True)
- Incremental embedding recomputation
- Graph update without full rebuild

### 6. Version Diffing
- Comparing two dataset versions
- Identifying added, removed, and modified files
- File-level change detection using hashes
- Impact analysis for updates

### 7. Filtered Query
- Filtering by dataset version
- Filtering by source URI or type
- Minimum similarity score threshold
- Combining multiple filters

### 8. Graph Relationships
- Exploring graph neighbors
- Graph walk with configurable depth
- Relationship types (adjacent, semantic, references)
- Node retrieval from graph

### 9. Exporting Lineage Data
- Exporting graph as JSON
- Node and edge information
- Relationship types
- Complete lineage structure

### 10. Dataset Versioning
- Viewing version history
- File tracking per version
- Version metadata
- Current version information

## Running the Example

```bash
# From repository root
python examples/comprehensive_example.py

# Or if installed
python -m examples.comprehensive_example
```

## Expected Output

The example will demonstrate:
- Building a database from sample files
- Querying and retrieving results with full lineage
- Auditing answers for quality and consistency
- Updating incrementally
- Comparing versions
- Exploring graph relationships
- Exporting lineage data

## Key Concepts

### Lineage Node (LN)
Every retrievable chunk is a Lineage Node with:
- Immutable ID
- Source reference
- Transform chain
- Content hash
- Dataset version
- Timestamps

### Lineage Graph
A DAG (Directed Acyclic Graph) linking nodes through:
- Adjacent relationships (chunks from same source)
- Semantic relationships (similar content)
- Reference relationships (citations)
- Entity relationships (same entity mentions)

### Dataset Versioning
Each build creates a versioned manifest tracking:
- All source files and their hashes
- File modification times
- Version metadata
- Build information

### Answer Auditing
Every answer can be audited for:
- Version consistency (all from same version?)
- Staleness (using outdated data?)
- Transform risks (aggressive normalization, OCR errors, etc.)

## Use Cases

1. **Production RAG Systems**: Track provenance for compliance
2. **Answer Debugging**: Understand why answers changed
3. **Data Updates**: Incrementally update without full rebuild
4. **Quality Assurance**: Audit answers before deployment
5. **Compliance**: Maintain audit trails for regulatory requirements
