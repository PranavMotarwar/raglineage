"""I/O utilities for file operations."""

import json
from pathlib import Path
from typing import Any, Union

from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


def ensure_dir(path: Path | str) -> Path:
    """
    Ensure directory exists, creating if necessary.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(file_path: Path | str) -> Any:
    """
    Load JSON from file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning(f"JSON file not found: {file_path}")
        return None
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, file_path: Path | str, indent: int = 2) -> None:
    """
    Save data as JSON to file.

    Args:
        data: Data to serialize
        file_path: Path to save JSON file
        indent: JSON indentation
    """
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
