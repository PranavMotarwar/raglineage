"""PDF parsing and public workflows, using real minimal PDF documents."""

import json
import sys

import pytest
from typer.testing import CliRunner

from raglineage import RagLineage
from raglineage.cli.main import app
from raglineage.ingest import AutoIngestor, PDFIngestor
from raglineage.retrieval.filters import FilterConfig
from raglineage.schemas.lineage_node import PDFSource
from raglineage.utils.hashing import compute_content_hash


def write_pdf(path, pages, password=None):
    pypdf = pytest.importorskip("pypdf")
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = pypdf.PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        if text is not None:
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
            })
            stream = DecodedStreamObject()
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream.set_data(f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode())
            page[NameObject("/Contents")] = writer._add_object(stream)
    if password:
        writer.encrypt(password)
    writer.write(path)
    return path


def test_optional_dependency_and_recognition(tmp_path, monkeypatch):
    pdf = tmp_path / "guide.PDF"
    pdf.write_bytes(b"%PDF")
    assert AutoIngestor().can_ingest(pdf)
    assert not PDFIngestor().can_ingest(tmp_path)
    assert not PDFIngestor().can_ingest(tmp_path / "missing.pdf")
    assert list(PDFIngestor().ingest(tmp_path / "missing.pdf")) == []
    monkeypatch.setitem(sys.modules, "pypdf", None)
    with pytest.raises(ImportError, match=r"raglineage\[pdf\]"):
        list(AutoIngestor().ingest(pdf))
    text = tmp_path / "guide.txt"
    text.write_text("Text still works without pypdf.")
    assert list(AutoIngestor().ingest(text))


def test_pages_ids_hashes_and_blank_warning(tmp_path, caplog):
    pdf = write_pdf(tmp_path / "guide.PDF", ["Repeated text", None, "Repeated text"])
    nodes = list(AutoIngestor("v2").ingest(pdf))
    assert [n.source.page for n in nodes] == [1, 3]
    assert all(isinstance(n.source, PDFSource) for n in nodes)
    assert all(n.source.uri == str(pdf) and n.dataset_version == "v2" for n in nodes)
    assert all(n.transform_chain == ["pdf_parse"] for n in nodes)
    assert all(n.content_hash == compute_content_hash(n.content) for n in nodes)
    assert len({n.ln_id for n in nodes}) == 2
    assert [n.ln_id for n in nodes] == [n.ln_id for n in PDFIngestor().ingest(pdf)]
    copy = write_pdf(tmp_path / "other.pdf", ["Repeated text"])
    assert next(PDFIngestor().ingest(copy)).ln_id != nodes[0].ln_id
    assert "page 2" in caplog.text and "OCR" in caplog.text


@pytest.mark.parametrize("strategy", ["simple", "semantic"])
def test_chunking_retrieval_exports_reload_and_update(tmp_path, strategy):
    pdf = write_pdf(tmp_path / "policy.pdf", [
        "Refunds are available for thirty days. Contact support for refunds. " * 3,
        "The warranty lasts two years. Warranty repairs are free. " * 3,
    ])
    rag = RagLineage(pdf, chunk_size=75, chunk_overlap=10, chunking_strategy=strategy)
    rag.build("v1")
    assert {n.source.page for n in rag.node_registry.values()} == {1, 2}
    assert all("pdf_parse" in n.transform_chain for n in rag.node_registry.values())
    loaded = RagLineage(pdf)
    hits = loaded.retrieve("warranty", k=1, filters=FilterConfig(source_type="pdf"))
    assert hits and hits[0].source.page == 2
    assert "page 2" in loaded.format_context_for_llm(hits)
    assert "page 2" not in loaded.format_context_for_llm(hits, include_sources=False)
    answer = loaded.query("warranty", k=1)
    assert "page 2" in answer.to_markdown()
    assert json.loads(answer.model_dump_json())["lineage"][0]["source"]["page"] == 2
    assert loaded.audit(answer).staleness_check == "pass"
    write_pdf(pdf, ["Refund period is now sixty days."])
    loaded.update("v2")
    current = RagLineage(pdf)
    assert current.retrieve("Refund", k=1)[0].source.page == 1
    assert {n.source.page for n in current.node_registry.values()} == {1}
    assert current.diff("v1", "v2").modified_files == ["policy.pdf"]
    assert all(n.dataset_version == "v2" for n in current.node_registry.values())


@pytest.mark.parametrize("failure", ["encrypted", "corrupt", "empty"])
def test_failed_build_preserves_persisted_version(tmp_path, failure):
    pdf = write_pdf(tmp_path / "policy.pdf", ["Original policy."])
    RagLineage(pdf).build("v1")
    if failure == "encrypted":
        write_pdf(pdf, ["Secret"], password="password")
        expected = "Encrypted PDFs"
    elif failure == "corrupt":
        pdf.write_bytes(b"not a PDF")
        expected = "Failed to ingest PDF"
    else:
        write_pdf(pdf, [None])
        expected = "no ingestible"
    with pytest.raises(ValueError, match=expected):
        RagLineage(pdf).build("v2")
    loaded = RagLineage(pdf)
    assert loaded.stats().current_version == "v1"
    assert loaded.stats().versions == ["v1"]
    assert loaded.retrieve("Original", k=1)[0].source.page == 1


def test_mixed_directory_exclusions_and_cli(tmp_path):
    write_pdf(tmp_path / "policy.pdf", ["Refund period is thirty days."])
    (tmp_path / "notes.txt").write_text("Contact the support team.")
    (tmp_path / "broken.pdf").write_bytes(b"broken")
    rag = RagLineage(tmp_path)
    rag.build("v1", exclude=["broken.pdf"])
    assert {n.source.type for n in rag.node_registry.values()} == {"file", "pdf"}
    runner = CliRunner()
    for command, output in [("retrieve", "json"), ("retrieve", "llm"),
                            ("retrieve", "table"), ("query", "json"), ("query", "table")]:
        result = runner.invoke(app, [command, "Refund", "--source", str(tmp_path),
                                     "--k", "1", "--output", output], terminal_width=160)
        assert result.exit_code == 0, result.output
        if output == "json":
            body = json.loads(result.output)
            entries = body["hits" if command == "retrieve" else "lineage"]
            assert entries[0]["source"]["page"] == 1
        else:
            assert "page 1" in result.output


def test_partial_extraction_failure_does_not_publish(tmp_path, monkeypatch):
    pypdf = pytest.importorskip("pypdf")
    pdf = write_pdf(tmp_path / "guide.pdf", ["Old policy."])
    RagLineage(pdf).build("v1")
    write_pdf(pdf, ["Replacement policy.", "Broken second page."])
    original = pypdf.PageObject.extract_text

    def fail_second(page, *args, **kwargs):
        text = original(page, *args, **kwargs)
        if "Broken" in text:
            raise RuntimeError("text extraction failed")
        return text

    monkeypatch.setattr(pypdf.PageObject, "extract_text", fail_second)
    with pytest.raises(ValueError, match="text extraction failed"):
        RagLineage(pdf).update("v2")
    loaded = RagLineage(pdf)
    assert loaded.stats().current_version == "v1"
    assert "Old policy" in loaded.retrieve("policy", k=1)[0].content


def test_cli_build_and_documented_example(tmp_path):
    import subprocess

    pdf = write_pdf(tmp_path / "guide.pdf", ["Refunds are allowed for thirty days."])
    result = CliRunner().invoke(app, ["build", "--source", str(pdf), "--version", "v1"])
    assert result.exit_code == 0, result.output
    result = subprocess.run(
        [sys.executable, "examples/basic_usage/pdf_example.py", str(pdf),
         "--question", "refunds"], capture_output=True, text=True, check=True,
    )
    assert "page 1" in result.stdout
    assert "pdf_parse" in result.stdout or '"staleness_check": "pass"' in result.stdout


def test_empty_pdf_and_missing_extra_do_not_create_version(tmp_path, monkeypatch):
    pdf = write_pdf(tmp_path / "empty.pdf", [])
    rag = RagLineage(pdf)
    with pytest.raises(ValueError, match="no ingestible"):
        rag.build("empty")
    assert rag.stats().versions == []
    monkeypatch.setitem(sys.modules, "pypdf", None)
    with pytest.raises(ImportError, match=r"raglineage\[pdf\]"):
        RagLineage(pdf).build("missing")
    assert RagLineage(pdf).stats().versions == []
