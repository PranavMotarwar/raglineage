# Basic Usage Example

## PDF usage with page citations

```bash
pip install "raglineage[pdf]"
python examples/basic_usage/pdf_example.py /path/to/handbook.pdf --question "What is the refund policy?"
```

Run from the repository root. You can also pass a directory containing PDFs
and supported text/tabular files. The example builds an offline NumPy/hash
index, queries it, prints Markdown and individual page citations, formats
context for your own LLM, and audits the answer.

PDF citations use physical pages starting at 1; chunking never crosses page
boundaries. Scanned pages require OCR beforehand; blank or image-only pages
are skipped with warnings. Encrypted and unreadable PDFs fail with an actionable
error. Identical chunks may be deduplicated, retaining one source occurrence.

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
