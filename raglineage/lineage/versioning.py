from typing import Union
"""Dataset versioning and manifest management."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from raglineage.schemas.dataset import DatasetManifest, DatasetVersion, FileEntry
from raglineage.utils.hashing import compute_file_hash
from raglineage.utils.io import ensure_dir, load_json, save_json
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)

MANIFEST_DIR = ".raglineage"
MANIFEST_FILE = "manifest.json"


class VersionStore:
    """Manages dataset versions and manifests."""

    def __init__(self, root_path: Union[Path, str]) -> None:
        """
        Initialize version store.

        Args:
            root_path: Root directory of the dataset
        """
        self.root_path = Path(root_path)
        self.manifest_path = self.root_path / MANIFEST_DIR / MANIFEST_FILE
        self._manifest: Optional[DatasetManifest] = None

    def load_manifest(self) -> Optional[DatasetManifest]:
        """
        Load manifest from disk.

        Returns:
            Dataset manifest or None if not found
        """
        if self._manifest is not None:
            return self._manifest

        data = load_json(self.manifest_path)
        if data is None:
            return None

        try:
            self._manifest = DatasetManifest.model_validate(data)
            return self._manifest
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return None

    def save_manifest(self, manifest: DatasetManifest) -> None:
        """
        Save manifest to disk.

        Args:
            manifest: Dataset manifest to save
        """
        ensure_dir(self.manifest_path.parent)
        save_json(manifest.model_dump(mode="json"), self.manifest_path)
        self._manifest = manifest
        logger.info(f"Saved manifest: {self.manifest_path}")

    def create_manifest(self, dataset_name: str) -> DatasetManifest:
        """
        Create a new manifest.

        Args:
            dataset_name: Name of the dataset

        Returns:
            New dataset manifest
        """
        manifest = DatasetManifest(dataset_name=dataset_name)
        self.save_manifest(manifest)
        return manifest

    def get_or_create_manifest(self, dataset_name: str) -> DatasetManifest:
        """
        Get existing manifest or create new one.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dataset manifest
        """
        manifest = self.load_manifest()
        if manifest is None:
            manifest = self.create_manifest(dataset_name)
        return manifest

    def create_version(
        self, version: str, files: list[Path], metadata: dict[str, Any] Optional[ = None
    ) -> DatasetVersion:
        """
        Create a new dataset version.

        Args:
            version: Version tag
            files: List of file paths (relative to root)
            metadata: Optional version metadata

        Returns:
            New dataset version
        """
        file_entries = []
        for file_path in files:
            full_path = self.root_path / file_path
            if full_path.exists():
                file_entries.append(
                    FileEntry(
                        path=str(file_path),
                        hash=compute_file_hash(full_path),
                        size=full_path.stat().st_size,
                        modified_at=datetime.fromtimestamp(full_path.stat().st_mtime),
                    )
                )

        version_obj = DatasetVersion(
            version=version,
            created_at=datetime.utcnow(),
            files=file_entries,
            metadata=metadata or {},
        )

        manifest = self.get_or_create_manifest(self.root_path.name)
        manifest.add_version(version_obj)
        self.save_manifest(manifest)

        return version_obj

    def get_version(self, version: str) -> Optional[DatasetVersion]:
        """
        Get a specific version.

        Args:
            version: Version tag

        Returns:
            Dataset version or None if not found
        """
        manifest = self.load_manifest()
        if manifest is None:
            return None
        return manifest.get_version(version)

    def get_current_version(self) -> Optional[str]:
        """
        Get current version tag.

        Returns:
            Current version or None
        """
        manifest = self.load_manifest()
        if manifest is None:
            return None
        return manifest.current_version
