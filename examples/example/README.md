# raglineage Example

This example shows how to use raglineage in practice. It walks through the main features you'll use day-to-day.

## What it covers

- Setting up raglineage with your data
- Building a versioned database
- Querying and getting results with full lineage
- Checking answer quality with auditing
- Updating incrementally when files change
- Comparing versions to see what changed
- Filtering results by version or other criteria
- Exploring relationships in the graph
- Exporting lineage data

## Running it

```bash
# From the repo root
python examples/example/example.py
```

## What you'll see

The example processes sample files, builds a database, runs some queries, and shows you the lineage information for each result. You'll see how every chunk tracks where it came from, what transforms were applied, and which version it belongs to.

## The key idea

Every chunk in raglineage is a Lineage Node that remembers:
- Where it came from (file, page, row, etc.)
- What transforms were applied
- Which dataset version it's from
- How it relates to other chunks (via the graph)

This makes it possible to audit answers, track changes, and understand exactly where your results came from.
