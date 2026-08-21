"""CLI main entry point using typer."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from raglineage import RagLineage, __version__
from raglineage.retrieval.filters import FilterConfig
from raglineage.utils.logging import get_logger

app = typer.Typer(help="raglineage - Lineage-aware RAG engine")
console = Console()
logger = get_logger(__name__)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    show_version: bool = typer.Option(False, "--version", help="Show version and exit"),
) -> None:
    """raglineage - Lineage-aware RAG engine."""
    if show_version:
        console.print(__version__)
        raise typer.Exit()


@app.command()
def init(path: str = typer.Argument(..., help="Path to initialize")) -> None:
    """Initialize a new raglineage project."""
    project_path = Path(path)
    project_path.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Initialized raglineage project at: {project_path}")


@app.command()
def build(
    source: str = typer.Option(..., "--source", "-s", help="Source directory or file"),
    version: str = typer.Option("v1.0", "--version", "-v", help="Dataset version"),
    store_backend: str = typer.Option("faiss", "--store-backend", help="Vector store backend: faiss or numpy"),
    chunk_size: int = typer.Option(1000, "--chunk-size", help="Chunk size"),
    chunk_overlap: int = typer.Option(200, "--chunk-overlap", help="Chunk overlap"),
    exclude: list[str] = typer.Option([], "--exclude", "-e", help="Exclude pattern (e.g. *.log, .git; repeatable)"),
) -> None:
    """Build RAG database from source."""
    console.print(f"[cyan]Building RAG database from: {source}")
    rag = RagLineage(
        source=source,
        store_backend=store_backend,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    rag.build(version=version, exclude=exclude or None)
    console.print(f"[green]Build complete: version {version}")


@app.command()
def update(
    source: str = typer.Option(..., "--source", "-s", help="Source directory or file"),
    version: str = typer.Option(..., "--version", "-v", help="New dataset version"),
    changed_only: bool = typer.Option(True, "--changed-only/--all", help="Only process changed files"),
) -> None:
    """Update RAG database incrementally."""
    console.print(f"[cyan]Updating RAG database: {source}")
    rag = RagLineage(source=source)
    rag.update(version=version, changed_only=changed_only)
    console.print(f"[green]Update complete: version {version}")


@app.command()
def query(
    question: str = typer.Argument(..., help="Query question"),
    source: str = typer.Option(..., "--source", "-s", help="Source directory"),
    k: int = typer.Option(5, "--k", help="Number of results"),
    version: str = typer.Option(None, "--version", help="Filter by dataset version"),
    min_score: float = typer.Option(0.0, "--min-score", help="Minimum similarity score (0–1)"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
) -> None:
    """Query the RAG database."""
    rag = RagLineage(source=source)

    filters = None
    if version is not None or min_score > 0:
        filters = FilterConfig(dataset_version=version, min_score=min_score)

    answer = rag.query(question, k=k, filters=filters)
    report = rag.audit(answer)

    if output == "json":
        import json
        out = {
            "question": answer.question,
            "answer": answer.answer,
            "lineage": [e.model_dump(mode="json") for e in answer.lineage],
            "audit": report.model_dump(mode="json"),
        }
        console.print(json.dumps(out, indent=2))
        return

    console.print(f"\n[bold]Question:[/bold] {answer.question}")
    console.print(f"\n[bold]Answer:[/bold] {answer.answer}")
    console.print(f"\n[bold]Lineage:[/bold] {len(answer.lineage)} nodes")

    # Show lineage table
    if answer.lineage:
        table = Table(title="Lineage")
        table.add_column("LN ID", style="cyan")
        table.add_column("Score", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Source", style="magenta")

        for entry in answer.lineage:
            uri = getattr(entry.source, "uri", str(entry.source))
            table.add_row(
                entry.ln_id[:12] + "...",
                f"{entry.score:.3f}",
                entry.dataset_version,
                uri[:50] + "..." if len(uri) > 50 else uri,
            )

        console.print(table)

    console.print(f"\n[bold]Audit Report:[/bold]")
    console.print(f"  Staleness: {report.staleness_check}")
    console.print(f"  Version Consistency: {report.version_consistency}")
    if report.transform_risk_flags:
        console.print(f"  Risk Flags: {', '.join(report.transform_risk_flags)}")


@app.command("retrieve")
def retrieve_chunks(
    question: str = typer.Argument(..., help="Query text"),
    source: str = typer.Option(..., "--source", "-s", help="Source directory"),
    k: int = typer.Option(5, "--k", help="Number of hits"),
    version: str = typer.Option(None, "--version", help="Filter by dataset version"),
    min_score: float = typer.Option(0.0, "--min-score", help="Minimum similarity score (0–1)"),
    output: str = typer.Option(
        "json",
        "--output",
        "-o",
        help="Output: json (hits), llm (formatted context only), table",
    ),
) -> None:
    """Retrieve chunks with lineage (no synthetic answer). For piping into your own LLM."""
    import json

    rag = RagLineage(source=source)
    filters = None
    if version is not None or min_score > 0:
        filters = FilterConfig(dataset_version=version, min_score=min_score)
    hits = rag.retrieve(question, k=k, filters=filters)

    if output == "llm":
        console.print(RagLineage.format_context_for_llm(hits))
        return
    if output == "json":
        out = {
            "question": question,
            "hits": [h.model_dump(mode="json") for h in hits],
            "formatted_context": RagLineage.format_context_for_llm(hits),
        }
        console.print(json.dumps(out, indent=2))
        return

    table = Table(title="Retrieval hits")
    table.add_column("Score", style="green")
    table.add_column("LN ID", style="cyan")
    table.add_column("Version", style="yellow")
    table.add_column("Source", style="magenta")
    for h in hits:
        uri = getattr(h.source, "uri", str(h.source))
        table.add_row(f"{h.score:.3f}", h.ln_id[:16] + "...", h.dataset_version, uri[:48])
    console.print(table)


@app.command()
def serve(
    source: str = typer.Option(..., "--source", "-s", help="Source directory with built dataset"),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8765, "--port", help="Bind port"),
    store_backend: str = typer.Option("faiss", "--store-backend", help="faiss or numpy"),
) -> None:
    """Run HTTP API (FastAPI): GET /health, /stats; POST /query, /retrieve. Requires: pip install raglineage[serve]"""
    try:
        import uvicorn  # noqa: WPS433

        from raglineage.serve.app import create_app
    except ImportError:
        console.print("[red]Missing dependency. Install with: pip install raglineage[serve][/red]")
        raise typer.Exit(1)

    app = create_app(source=source, store_backend=store_backend)
    console.print(f"[cyan]raglineage API[/cyan] http://{host}:{port}  (docs: /docs)")
    uvicorn.run(app, host=host, port=port)


@app.command()
def validate(
    source: str = typer.Option(..., "--source", "-s", help="Source directory"),
) -> None:
    """Validate dataset: check build status and exit 0 if OK, 1 otherwise (for CI)."""
    rag = RagLineage(source=source)
    s = rag.stats()
    if not s.is_built:
        console.print("[red]Validation failed: dataset not built. Run 'raglineage build' first.[/red]")
        raise typer.Exit(1)
    if s.node_count == 0:
        console.print("[red]Validation failed: no lineage nodes. Rebuild with non-empty source.[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Valid: {s.node_count} nodes, version {s.current_version}[/green]")


@app.command()
def stats(
    source: str = typer.Option(..., "--source", "-s", help="Source directory"),
) -> None:
    """Show dataset statistics (node count, versions, build status)."""
    rag = RagLineage(source=source)
    s = rag.stats()

    console.print("\n[bold]raglineage Dataset Stats[/bold]")
    console.print(f"  Built: {s.is_built}")
    console.print(f"  Nodes: {s.node_count}")
    console.print(f"  Current version: {s.current_version or 'N/A'}")
    console.print(f"  Source files: {s.source_files}")
    console.print(f"  All versions: {', '.join(s.versions) if s.versions else 'None'}")
    console.print(f"  Storage: {s.storage_path}")


@app.command()
def diff(
    version_from: str = typer.Argument(..., help="Source version"),
    version_to: str = typer.Argument(..., help="Target version"),
    source: str = typer.Option(..., "--source", "-s", help="Source directory"),
) -> None:
    """Diff two dataset versions."""
    rag = RagLineage(source=source)
    diff_result = rag.diff(version_from, version_to)

    console.print(f"\n[bold]Version Diff:[/bold] {version_from} → {version_to}")
    console.print(f"  Added files: {len(diff_result.added_files)}")
    console.print(f"  Removed files: {len(diff_result.removed_files)}")
    console.print(f"  Modified files: {len(diff_result.modified_files)}")
    console.print(f"  Unchanged files: {len(diff_result.unchanged_files)}")

    if diff_result.added_files:
        console.print("\n[green]Added:[/green]")
        for f in diff_result.added_files:
            console.print(f"  + {f}")

    if diff_result.removed_files:
        console.print("\n[red]Removed:[/red]")
        for f in diff_result.removed_files:
            console.print(f"  - {f}")

    if diff_result.modified_files:
        console.print("\n[yellow]Modified:[/yellow]")
        for f in diff_result.modified_files:
            console.print(f"  ~ {f}")


if __name__ == "__main__":
    app()
