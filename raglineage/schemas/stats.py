"""Stats and summary schemas for dataset overview."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class RagLineageStats(BaseModel):
    """Statistics for a raglineage dataset."""

    node_count: int = Field(..., description="Number of lineage nodes in the graph")
    current_version: Optional[str] = Field(None, description="Current dataset version")
    source_files: int = Field(..., description="Number of source files in current version")
    versions: list[str] = Field(
        default_factory=list, description="List of all dataset versions"
    )
    storage_path: Path | str = Field(..., description="Path to .raglineage storage")
    is_built: bool = Field(..., description="Whether the RAG database has been built")
