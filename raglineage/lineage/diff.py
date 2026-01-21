"""Version diffing and change detection."""

from typing import Any

from raglineage.schemas.dataset import DatasetVersion
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class VersionDiff:
    """Result of diffing two dataset versions."""

    def __init__(
        self,
        version_from: str,
        version_to: str,
        added_files: list[str],
        removed_files: list[str],
        modified_files: list[str],
        unchanged_files: list[str],
    ) -> None:
        """
        Initialize version diff.

        Args:
            version_from: Source version
            version_to: Target version
            added_files: Files added in target version
            removed_files: Files removed in target version
            modified_files: Files modified (hash changed)
            unchanged_files: Files unchanged
        """
        self.version_from = version_from
        self.version_to = version_to
        self.added_files = added_files
        self.removed_files = removed_files
        self.modified_files = modified_files
        self.unchanged_files = unchanged_files

    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return (
            len(self.added_files) > 0
            or len(self.removed_files) > 0
            or len(self.modified_files) > 0
        )

    def get_changed_files(self) -> list[str]:
        """Get all changed files (added, removed, modified)."""
        return self.added_files + self.removed_files + self.modified_files

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_from": self.version_from,
            "version_to": self.version_to,
            "added_files": self.added_files,
            "removed_files": self.removed_files,
            "modified_files": self.modified_files,
            "unchanged_files": self.unchanged_files,
        }


def compute_diff(version_from: DatasetVersion, version_to: DatasetVersion) -> VersionDiff:
    """
    Compute diff between two dataset versions.

    Args:
        version_from: Source version
        version_to: Target version

    Returns:
        VersionDiff object
    """
    files_from = {f.path: f.hash for f in version_from.files}
    files_to = {f.path: f.hash for f in version_to.files}

    added_files = [path for path in files_to if path not in files_from]
    removed_files = [path for path in files_from if path not in files_to]
    modified_files = [
        path
        for path in files_from
        if path in files_to and files_from[path] != files_to[path]
    ]
    unchanged_files = [
        path
        for path in files_from
        if path in files_to and files_from[path] == files_to[path]
    ]

    return VersionDiff(
        version_from=version_from.version,
        version_to=version_to.version,
        added_files=added_files,
        removed_files=removed_files,
        modified_files=modified_files,
        unchanged_files=unchanged_files,
    )
