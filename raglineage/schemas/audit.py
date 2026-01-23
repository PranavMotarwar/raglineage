"""Audit schemas for answer lineage and audit reports."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from raglineage.schemas.lineage_node import SourceRef


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
