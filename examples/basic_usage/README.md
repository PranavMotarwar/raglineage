# Basic Usage Example

A minimal example to get started with raglineage.

## What it does

1. Builds a RAG database from sample files
2. Queries the database
3. Shows the lineage for each result
4. Audits the answer for quality

## Running it

```bash
python examples/basic_usage/example.py
```

## What you'll see

The example builds a database, runs a query, and prints out the answer along with detailed lineage information showing where each chunk came from and what transforms were applied.
