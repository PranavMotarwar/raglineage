"""Regression tests for workflows that cross process/object boundaries."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from raglineage import RagLineage
from raglineage.cli.main import app
from raglineage.embedding import local
from raglineage.lineage.versioning import VersionStore
from raglineage.serve.app import create_app


def force_offline_embedder(monkeypatch) -> None:
    # Hash embeddings are the safe, dependency-free default.
    assert local.LocalEmbedder("hash").model is None


def test_numpy_build_can_be_loaded_and_queried(tmp_path: Path, monkeypatch) -> None:
    force_offline_embedder(monkeypatch)
    source = tmp_path / "docs"
    source.mkdir()
    (source / "policy.txt").write_text(
        "Retrieval audit records are retained for 90 days.", encoding="utf-8"
    )

    RagLineage(source, store_backend="numpy").build(version="v1.0")

    loaded = RagLineage(source, store_backend="numpy")
    hits = loaded.retrieve("How many days are audit records retained?", k=1)
    answer = loaded.query("How many days are audit records retained?", k=1)
    assert hits and "90 days" in hits[0].content
    assert answer.lineage
    assert answer.metadata["answer_mode"] == "extractive"
    assert answer.answer == hits[0].content
    assert loaded.stats().is_built
    assert (source / ".raglineage" / "numpy_index.npy").exists()


def test_update_excludes_internal_state_and_manifest_remains_loadable(
    tmp_path: Path, monkeypatch
) -> None:
    force_offline_embedder(monkeypatch)
    source = tmp_path / "docs"
    source.mkdir()
    document = source / "runbook.txt"
    document.write_text("The release is blue.", encoding="utf-8")
    RagLineage(source, store_backend="numpy").build(version="v1.0")

    document.write_text("The release is green.", encoding="utf-8")
    RagLineage(source, store_backend="numpy").update(version="v1.1")

    manifest = VersionStore(source).load_manifest()
    assert manifest is not None
    latest = manifest.get_version("v1.1")
    assert latest is not None
    assert [entry.path for entry in latest.files] == ["runbook.txt"]
    assert RagLineage(source, store_backend="numpy").diff("v1.0", "v1.1").modified_files == [
        "runbook.txt"
    ]


def test_update_persists_deleted_source_removal(tmp_path: Path, monkeypatch) -> None:
    force_offline_embedder(monkeypatch)
    source = tmp_path / "docs"
    source.mkdir()
    document = source / "obsolete.txt"
    document.write_text("This content must disappear.", encoding="utf-8")
    RagLineage(source, store_backend="numpy").build(version="v1.0")

    document.unlink()
    RagLineage(source, store_backend="numpy").update(version="v1.1")

    loaded = RagLineage(source, store_backend="numpy")
    assert loaded.retrieve("content", k=5) == []
    assert loaded.stats().node_count == 0


def test_legacy_manifest_timestamp_is_repaired(tmp_path: Path) -> None:
    source = tmp_path / "docs"
    state = source / ".raglineage"
    state.mkdir(parents=True)
    (state / "manifest.json").write_text(
        json.dumps(
            {
                "dataset_name": "docs",
                "current_version": None,
                "versions": [],
                "created_at": "2026-08-21T07:09:48.470933+00:00Z",
                "updated_at": "2026-08-21T07:09:48.470933+00:00Z",
                "metadata": {},
            }
        ),
        encoding="utf-8",
    )
    assert VersionStore(source).load_manifest() is not None


def test_init_scaffolds_a_usable_project(tmp_path: Path) -> None:
    target = tmp_path / "project"
    result = CliRunner().invoke(app, ["init", str(target)])
    assert result.exit_code == 0
    assert (target / "docs").is_dir()
    assert (target / "raglineage.yaml").is_file()
    assert (target / "README.md").is_file()


def test_http_api_reads_a_persisted_numpy_dataset(tmp_path: Path, monkeypatch) -> None:
    force_offline_embedder(monkeypatch)
    source = tmp_path / "docs"
    source.mkdir()
    (source / "policy.txt").write_text("Support is available on Fridays.", encoding="utf-8")
    RagLineage(source, store_backend="numpy").build(version="v1.0")

    client = TestClient(create_app(str(source), store_backend="numpy"))
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/stats").json()["node_count"] == 1
    response = client.post(
        "/retrieve",
        json={"question": "When is support available?", "k": 1, "format_llm": True},
    )
    assert response.status_code == 200
    assert response.json()["hits"][0]["dataset_version"] == "v1.0"
    assert "Fridays" in response.json()["formatted_context"]
