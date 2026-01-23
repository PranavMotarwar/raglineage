# Basic Usage Example

This example demonstrates the core functionality of raglineage.

## Prerequisites

Install raglineage:

```bash
pip install raglineage
```

## Running the Example

From the repository root:

```bash
python examples/basic_usage/example.py
```

Or if installed:

```bash
python -m examples.basic_usage.example
```

## What This Example Does

1. **Initializes raglineage** with sample data from `examples/data/`
2. **Builds a RAG database** (version v1.0) from text and CSV files
3. **Queries the database** with a question about refund policy
4. **Shows lineage information** for each retrieved chunk
5. **Audits the answer** for staleness and version consistency
6. **Displays JSON output** of the answer and audit report

## Expected Output

The example will:
- Build the database from source files
- Retrieve relevant chunks with scores
- Show complete lineage (source, version, transforms)
- Display audit results
- Output JSON representations

## Files Used

The example uses files from `examples/data/`:
- `sample.txt` - Sample text file with policies
- `products.csv` - Sample CSV file with product data
