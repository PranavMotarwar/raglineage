"""CLI main entry point using typer."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from raglineage import RagLineage
from raglineage.lineage.diff import VersionDiff
from raglineage.retrieval.filters import FilterConfig
from raglineage.utils.logging import get_logger

app = typer.Typer(help="raglineage - Lineage-aware RAG engine")
console = Console()
logger = get_logger(__name__)


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
    chunk_size: int = typer.Option(1000, "--chunk-size", help="Chunk size"),
    chunk_overlap: int = typer.Option(200, "--chunk-overlap", help="Chunk overlap"),
) -> None:
    """Build RAG database from source."""
    console.print(f"[cyan]Building RAG database from: {source}")
    rag = RagLineage(
        source=source,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    rag.build(version=version)
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
) -> None:
    """Query the RAG database."""
    rag = RagLineage(source=source)

    filters = None
    if version:
        filters = FilterConfig(dataset_version=version)

    answer = rag.query(question, k=k, filters=filters)
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
            table.add_row(
                entry.ln_id[:12] + "...",
                f"{entry.score:.3f}",
                entry.dataset_version,
                entry.source.uri[:50] + "..." if len(entry.source.uri) > 50 else entry.source.uri,
            )

        console.print(table)

    # Audit
    report = rag.audit(answer)
    console.print(f"\n[bold]Audit Report:[/bold]")
    console.print(f"  Staleness: {report.staleness_check}")
    console.print(f"  Version Consistency: {report.version_consistency}")
    if report.transform_risk_flags:
        console.print(f"  Risk Flags: {', '.join(report.transform_risk_flags)}")


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
