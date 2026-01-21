"""Lineage Node schema - the core data structure for lineage tracking."""

from datetime import datetime
from typing import Any, Literal, Union

from pydantic import BaseModel, Field


class FileSource(BaseModel):
    """Source reference for file-based data."""

    type: Literal["file"] = "file"
    uri: str = Field(..., description="File path or URI")
    line_start: int | None = Field(None, description="Starting line number")
    line_end: int | None = Field(None, description="Ending line number")


class PDFSource(BaseModel):
    """Source reference for PDF documents."""

    type: Literal["pdf"] = "pdf"
    uri: str = Field(..., description="PDF file path or URI")
    page: int = Field(..., description="Page number")
    section: str | None = Field(None, description="Section name or identifier")


class TabularSource(BaseModel):
    """Source reference for tabular data."""

    type: Literal["tabular"] = "tabular"
    uri: str = Field(..., description="Table file path or URI")
    row: int = Field(..., description="Row number (0-indexed)")
    column: str | None = Field(None, description="Column name")


class APISource(BaseModel):
    """Source reference for API data."""

    type: Literal["api"] = "api"
    uri: str = Field(..., description="API endpoint URL")
    request_id: str | None = Field(None, description="Request identifier")
    timestamp: str | None = Field(None, description="Request timestamp")


SourceRef = Union[FileSource, PDFSource, TabularSource, APISource]


class LineageNode(BaseModel):
    """
    Lineage Node - the atomic unit of retrieval with complete provenance.

    Every retrievable chunk is a Lineage Node with:
    - Immutable ID
    - Dataset version
    - Precise source reference
    - Full transform chain
    - Content hash
    - Timestamps
    """

    ln_id: str = Field(..., description="Stable, deterministic Lineage Node ID")
    content: str = Field(..., description="The actual text content")
    source: SourceRef = Field(..., description="Precise reference to origin")
    dataset_version: str = Field(..., description="Version tag for the dataset")
    transform_chain: list[str] = Field(
        default_factory=list, description="Ordered list of transforms applied"
    )
    content_hash: str = Field(
        ..., description="SHA-256 hash of content for integrity checking"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    def model_dump_json(self, **kwargs: Any) -> str:
        """Override to ensure datetime serialization."""
        return super().model_dump_json(**kwargs)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}
