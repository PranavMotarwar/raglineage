# raglineage Examples

This directory contains examples demonstrating raglineage functionality.

## Examples

### Basic Usage (`basic_usage/`)
A minimal example showing core functionality:
- Building a RAG database
- Querying with lineage
- Answer auditing

**Run:**
```bash
python examples/basic_usage/example.py
```

### Comprehensive Example (`comprehensive_example/`)
A complete demonstration of all raglineage features:
- Initialization and configuration
- Building with versioning
- Querying with lineage tracking
- Answer auditing
- Incremental updates
- Version diffing
- Filtered queries
- Graph relationships
- Exporting lineage data
- Dataset versioning

**Run:**
```bash
python examples/comprehensive_example/comprehensive_example.py
```

## Sample Data

The `data/` directory contains sample files used by the examples:
- `sample.txt` - Sample text file with policies
- `products.csv` - Sample CSV file with product data

## Key Features Demonstrated

### Lineage Tracking
Every retrievable chunk tracks:
- Exact source (file, page, row, URL)
- Full transform chain
- Dataset version
- Content hash
- Timestamps

### Dataset Versioning
- Track changes between versions
- File-level change detection
- Incremental updates
- Version comparison

### Answer Auditing
- Staleness detection
- Version consistency checks
- Transform risk flags
- Complete provenance reconstruction

### Graph Relationships
- DAG linking related chunks
- Graph-walk retrieval
- Relationship exploration
- Export capabilities

## Next Steps

1. Try the basic example to get started
2. Explore the comprehensive example for all features
3. Modify the examples for your use case
4. Check the main README for API documentation
