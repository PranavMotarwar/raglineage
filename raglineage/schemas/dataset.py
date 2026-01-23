"""Dataset manifest and versioning schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    """Entry for a file in a dataset version."""

    path: str = Field(..., description="File path relative to dataset root")
    hash: str = Field(..., description="SHA-256 hash of file contents")
    size: int = Field(..., description="File size in bytes")
    modified_at: datetime = Field(..., description="File modification timestamp")


class DatasetVersion(BaseModel):
    """Metadata for a dataset version."""

    version: str = Field(..., description="Version tag (e.g., 'v1.0')")
    created_at: datetime = Field(..., description="Version creation timestamp")
    files: list[FileEntry] = Field(default_factory=list, description="Files in this version")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Version-specific metadata"
    )


class DatasetManifest(BaseModel):
    """
    Dataset manifest stored in .raglineage/manifest.json.

    Tracks dataset name, versions, files, and build metadata.
    """

    dataset_name: str = Field(..., description="Name of the dataset")
    current_version: Optional[str] = Field(None, description="Current active version")
    versions: list[DatasetVersion] = Field(
        default_factory=list, description="List of all versions"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Manifest creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Dataset-level metadata"
    )

    def get_version(self, version: str) -> Optional[DatasetVersion]:
        """Get a specific version by tag."""
        for v in self.versions:
            if v.version == version:
                return v
        return None

    def add_version(self, version: DatasetVersion) -> None:
        """Add a new version to the manifest."""
        self.versions.append(version)
        self.current_version = version.version
        self.updated_at = datetime.utcnow()

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}
