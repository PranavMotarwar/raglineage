"""Pre-release scenarios modeled on real CLI and API usage."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from raglineage import RagLineage
from raglineage.cli.main import app
from raglineage.retrieval.filters import FilterConfig


def test_mixed_formats_exclusions_and_deterministic_rebuild(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("The launch region is Oregon.", encoding="utf-8")
    (docs / "plans.csv").write_text(
        "plan,price,company_contribution\n"
        "Starter,19,None\n"
        "Enterprise,99,None\n"
        "Retirement plan,0,50 percent match\n",
        encoding="utf-8",
    )
    (docs / "contacts.json").write_text(
        json.dumps([{"team": "Support", "email": "help@example.com"}]), encoding="utf-8"
    )
    (docs / "private.md").write_text("Secret launch code: quartz", encoding="utf-8")
    (docs / "ignored.bin").write_bytes(b"not an ingestible format")

    rag = RagLineage(docs)
    rag.build("v1.0", exclude=["private.md"])
    first_ids = set(rag.node_registry)
    first_count = rag.stats().node_count

    rebuilt = RagLineage(docs)
    assert rebuilt.config.store_backend == "numpy"
    assert rebuilt.config.embed_backend == "hash"
    rebuilt.build("v1.0", exclude=["private.md"])
    assert set(rebuilt.node_registry) == first_ids
    assert rebuilt.stats().node_count == first_count == 5
    assert rebuilt.stats().versions == ["v1.0"]
    assert all("private.md" not in entry.source.uri for entry in rebuilt.retrieve("quartz", k=4))
    region_hits = rebuilt.retrieve("Where is the US primary region?", k=2)
    assert "Oregon" in region_hits[0].content
    retirement_hits = rebuilt.retrieve("retirement company contribution", k=4)
    assert "Retirement plan" in retirement_hits[0].content


def test_update_is_complete_single_version_snapshot_and_reuses_excludes(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    stable = docs / "stable.txt"
    changed = docs / "changed.txt"
    excluded = docs / "draft.txt"
    stable.write_text("Stable owner is Alice.", encoding="utf-8")
    changed.write_text("Color is blue.", encoding="utf-8")
    excluded.write_text("Draft only content.", encoding="utf-8")
    RagLineage(docs).build("v1.0", exclude=["draft.txt"])

    changed.write_text("Color is green.", encoding="utf-8")
    RagLineage(docs).update("v1.1")

    current = RagLineage(docs)
    hits = current.retrieve("owner color", k=10)
    assert {hit.dataset_version for hit in hits} == {"v1.1"}
    assert len(hits) == 2
    assert all("draft.txt" not in hit.source.uri for hit in hits)
    assert current.diff("v1.0", "v1.1").modified_files == ["changed.txt"]


def test_single_file_source_persists_and_loads(tmp_path: Path) -> None:
    document = tmp_path / "handbook.md"
    document.write_text("Escalations go to the Reliability team.", encoding="utf-8")
    RagLineage(document).build("v1.0")

    loaded = RagLineage(document)
    assert loaded.stats().is_built
    assert loaded.retrieve("Who handles escalations?", k=1)[0].dataset_version == "v1.0"
    assert (tmp_path / ".handbook.md.raglineage" / "numpy_index.npy").exists()


def test_input_validation_is_actionable(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Source does not exist"):
        RagLineage(tmp_path / "missing")

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="No ingestible content"):
        RagLineage(empty).build()

    doc = tmp_path / "doc.txt"
    doc.write_text("Useful content.", encoding="utf-8")
    rag = RagLineage(doc)
    rag.build()
    with pytest.raises(ValueError, match="query must not be empty"):
        rag.retrieve(" ")
    with pytest.raises(ValueError, match="k must be greater than zero"):
        rag.retrieve("content", k=0)


def test_filters_remain_enforced_with_graph_expansion(tmp_path: Path) -> None:
    doc = tmp_path / "long.txt"
    doc.write_text(
        "Alpha policy applies to production. Beta policy applies only to staging.",
        encoding="utf-8",
    )
    rag = RagLineage(doc, chunk_size=38, chunk_overlap=5, graph_depth=2)
    rag.build("v1.0")
    assert rag.retrieve("policy", k=5, filters=FilterConfig(min_score=1.1)) == []
    assert rag.retrieve("policy", k=5, filters=FilterConfig(dataset_version="v9")) == []


def test_graph_expansion_cannot_outrank_its_seed_match(tmp_path: Path) -> None:
    source = tmp_path / "knowledge"
    source.mkdir()
    (source / "policy.md").write_text(
        "Vacation allowance is 20 days. " * 20
        + "A medical certificate is required after three consecutive sick days.",
        encoding="utf-8",
    )
    rag = RagLineage(source, chunk_size=120, chunk_overlap=20, graph_depth=1)
    rag.build(version="v1")

    hits = rag.retrieve("When is a medical certificate required?", k=1)

    assert "medical certificate" in hits[0].content.casefold()
    assert hits[0].score < 0.8


def test_cli_default_workflow_and_output_modes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    runner = CliRunner()
    assert runner.invoke(app, ["init", str(project)]).exit_code == 0
    (project / "docs" / "faq.txt").write_text(
        "Phone support opens at 8 AM Pacific.", encoding="utf-8"
    )

    build = runner.invoke(app, ["build", "--source", str(project / "docs")])
    assert build.exit_code == 0, build.output
    validate = runner.invoke(app, ["validate", "--source", str(project / "docs")])
    assert validate.exit_code == 0, validate.output
    as_json = runner.invoke(
        app,
        ["retrieve", "When does phone support open?", "--source", str(project / "docs")],
    )
    assert as_json.exit_code == 0, as_json.output
    assert json.loads(as_json.output)["hits"][0]["dataset_version"] == "v1.0"
    as_llm = runner.invoke(
        app,
        [
            "retrieve",
            "When does phone support open?",
            "--source",
            str(project / "docs"),
            "--output",
            "llm",
        ],
    )
    assert as_llm.exit_code == 0
    assert "8 AM Pacific" in as_llm.output


def test_faiss_backend_round_trip_when_installed(tmp_path: Path) -> None:
    pytest.importorskip("faiss")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "faq.txt").write_text("The warranty lasts two years.", encoding="utf-8")
    RagLineage(docs, store_backend="faiss").build("v1.0")
    hits = RagLineage(docs, store_backend="faiss").retrieve("warranty", k=1)
    assert hits and hits[0].dataset_version == "v1.0"
