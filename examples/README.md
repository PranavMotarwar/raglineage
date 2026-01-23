# raglineage Examples

Examples showing how to use raglineage.

## Examples

### Basic Usage (`basic_usage/`)
A quick start example that shows the essentials:
- Building a database
- Querying with lineage
- Auditing answers

**Run:**
```bash
python examples/basic_usage/example.py
```

### Full Example (`example/`)
A complete walkthrough of all features:
- Building with versioning
- Querying and lineage tracking
- Answer auditing
- Incremental updates
- Version comparison
- Filtering
- Graph exploration
- Exporting data

**Run:**
```bash
python examples/example/example.py
```

## Sample Data

The `data/` directory has sample files the examples use:
- `sample.txt` - Sample text with policies
- `products.csv` - Sample product data

## What raglineage does

raglineage tracks the complete lineage of every chunk in your RAG system. When you query, you get results with full provenance - you know exactly where each piece of information came from, what transforms were applied, and which version of your data it's from.

This makes it possible to:
- Audit answers for quality and consistency
- Track changes between dataset versions
- Update incrementally (only reprocess what changed)
- Understand why answers changed when data updates
- Maintain compliance trails
