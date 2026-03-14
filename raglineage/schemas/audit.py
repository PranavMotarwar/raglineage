"""Audit schemas for answer lineage and audit reports."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from raglineage.schemas.lineage_node import SourceRef


class RetrievalHit(BaseModel):
    """A single retrieved chunk with content and lineage. Use with your own LLM."""

    content: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Similarity score")
    ln_id: str = Field(..., description="Lineage Node ID")
    source: SourceRef = Field(..., description="Source reference")
    dataset_version: str = Field(..., description="Dataset version")
    transform_chain: list[str] = Field(default_factory=list, description="Transform chain")

    @staticmethod
    def format_context_for_llm(
        hits: list["RetrievalHit"],
        include_sources: bool = True,
        separator: str = "\n\n",
        max_content_chars: Optional[int] = None,
    ) -> str:
        """
        Format retrieved hits into a single context string for LLM prompts.

        Use with your own LLM: paste the returned string into a system or user message.

        Args:
            hits: List of RetrievalHit from rag.retrieve()
            include_sources: Prepend source URI to each chunk for citation
            separator: String between chunks
            max_content_chars: Truncate each chunk to this length (None = no limit)

        Returns:
            Formatted context string ready for prompt
        """
        parts = []
        for i, h in enumerate(hits, 1):
            text = h.content
            if max_content_chars and len(text) > max_content_chars:
                text = text[:max_content_chars] + "..."
            if include_sources:
                uri = getattr(h.source, "uri", str(h.source))
                parts.append(f"[{i}] (source: {uri})\n{text}")
            else:
                parts.append(f"[{i}]\n{text}")
        return separator.join(parts)


class LineageEntry(BaseModel):
    """A single lineage entry in an answer's provenance."""

    ln_id: str = Field(..., description="Lineage Node ID")
    score: float = Field(..., description="Retrieval score")
    source: SourceRef = Field(..., description="Source reference")
    dataset_version: str = Field(..., description="Dataset version")
    transform_chain: list[str] = Field(..., description="Transform chain")


class AnswerWithLineage(BaseModel):
    """Answer with complete lineage information."""

    question: str = Field(..., description="The query question")
    answer: str = Field(..., description="The generated answer")
    lineage: list[LineageEntry] = Field(
        default_factory=list, description="List of Lineage Nodes used"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional answer metadata"
    )

    def to_markdown(self) -> str:
        """
        Export answer and lineage to Markdown for reports and sharing.

        Returns:
            Markdown string suitable for reports, docs, or exports
        """
        lines = [
            f"## Question\n{self.question}",
            "",
            f"## Answer\n{self.answer}",
            "",
        ]
        if self.lineage:
            lines.append("## Lineage\n")
            lines.append("| LN ID | Score | Version | Source |")
            lines.append("|-------|-------|---------|--------|")
            for entry in self.lineage:
                full_uri = getattr(entry.source, "uri", str(entry.source))
                source_uri = full_uri[:60] + ("..." if len(full_uri) > 60 else "")
                lines.append(
                    f"| {entry.ln_id[:16]}... | {entry.score:.3f} | "
                    f"{entry.dataset_version} | {source_uri} |"
                )
        return "\n".join(lines)


class AuditReport(BaseModel):
    """Audit report for an answer."""

    answer_id: Optional[str] = Field(None, description="Answer identifier")
    staleness_check: Literal["pass", "fail", "warning"] = Field(
        ..., description="Staleness check result"
    )
    version_consistency: Literal[
        "single_version", "mixed_versions", "unknown"
    ] = Field(..., description="Version consistency status")
    transform_risk_flags: list[str] = Field(
        default_factory=list, description="Risk flags from transform chain analysis"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional audit metadata"
    )
