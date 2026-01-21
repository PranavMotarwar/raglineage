"""Hashing utilities for content and file integrity."""

import hashlib
from pathlib import Path


def compute_content_hash(content: str) -> str:
    """
    Compute SHA-256 hash of content.

    Args:
        content: Text content to hash

    Returns:
        SHA-256 hash as hex string with 'sha256:' prefix
    """
    hash_obj = hashlib.sha256(content.encode("utf-8"))
    return f"sha256:{hash_obj.hexdigest()}"


def compute_file_hash(file_path: Path | str) -> str:
    """
    Compute SHA-256 hash of file contents.

    Args:
        file_path: Path to file

    Returns:
        SHA-256 hash as hex string
    """
    file_path = Path(file_path)
    hash_obj = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()
