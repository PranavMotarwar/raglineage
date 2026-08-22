"""Minimal FastAPI app for query/stats over a built dataset."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from raglineage import RagLineage, __version__

try:
    from fastapi import FastAPI
except ImportError as e:  # pragma: no cover
    raise ImportError("Install raglineage with extra: pip install raglineage[serve]") from e


class QueryRequest(BaseModel):
    question: str = Field(..., description="Query text")
    k: int = Field(5, ge=1, le=100)
    dataset_version: Optional[str] = None
    min_score: float = Field(0.0, ge=0.0, le=1.0)


class RetrieveRequest(BaseModel):
    question: str
    k: int = Field(5, ge=1, le=100)
    dataset_version: Optional[str] = None
    min_score: float = Field(0.0, ge=0.0, le=1.0)
    format_llm: bool = Field(False, description="If true, include formatted_context string")


def create_app(
    source: str,
    store_backend: str | None = None,
    chunk_size: int = 400,
    chunk_overlap: int = 80,
) -> FastAPI:
    rag = RagLineage(
        source=source,
        store_backend=store_backend,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    app = FastAPI(
        title="raglineage",
        description="Lineage-aware RAG HTTP API",
        version=__version__,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/stats")
    def stats() -> dict[str, Any]:
        return rag.stats().model_dump(mode="json")

    @app.post("/query")
    def query(req: QueryRequest) -> dict[str, Any]:
        from raglineage.retrieval.filters import FilterConfig

        filters = FilterConfig(
            dataset_version=req.dataset_version,
            min_score=req.min_score,
        )
        answer = rag.query(req.question, k=req.k, filters=filters)
        report = rag.audit(answer)
        return {
            "question": answer.question,
            "answer": answer.answer,
            "lineage": [e.model_dump(mode="json") for e in answer.lineage],
            "audit": report.model_dump(mode="json"),
        }

    @app.post("/retrieve")
    def retrieve(req: RetrieveRequest) -> dict[str, Any]:
        from raglineage.retrieval.filters import FilterConfig

        filters = FilterConfig(
            dataset_version=req.dataset_version,
            min_score=req.min_score,
        )
        hits = rag.retrieve(req.question, k=req.k, filters=filters)
        out: dict[str, Any] = {
            "hits": [h.model_dump(mode="json") for h in hits],
        }
        if req.format_llm:
            out["formatted_context"] = RagLineage.format_context_for_llm(hits)
        return out

    return app
