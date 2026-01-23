"""Mapping between Lineage Node IDs and vector store indices."""

from typing import Optional

from raglineage.utils.io import load_json, save_json
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)


class LNMapping:
    """Maps Lineage Node IDs to vector store indices."""

    def __init__(self) -> None:
        """Initialize mapping."""
        self.ln_id_to_idx: dict[str, int] = {}
        self.idx_to_ln_id: dict[int, str] = {}
        self.next_idx = 0

    def add(self, ln_id: str) -> int:
        """
        Add a Lineage Node ID and return its index.

        Args:
            ln_id: Lineage Node ID

        Returns:
            Vector store index
        """
        if ln_id in self.ln_id_to_idx:
            return self.ln_id_to_idx[ln_id]

        idx = self.next_idx
        self.ln_id_to_idx[ln_id] = idx
        self.idx_to_ln_id[idx] = ln_id
        self.next_idx += 1
        return idx

    def get_idx(self, ln_id: str) -> Optional[int]:
        """Get index for a Lineage Node ID."""
        return self.ln_id_to_idx.get(ln_id)

    def get_ln_id(self, idx: int) -> Optional[str]:
        """Get Lineage Node ID for an index."""
        return self.idx_to_ln_id.get(idx)

    def remove(self, ln_id: str) -> None:
        """Remove a Lineage Node ID from mapping."""
        if ln_id in self.ln_id_to_idx:
            idx = self.ln_id_to_idx[ln_id]
            del self.ln_id_to_idx[ln_id]
            del self.idx_to_ln_id[idx]

    def save(self, path: str) -> None:
        """Save mapping to JSON file."""
        data = {
            "ln_id_to_idx": self.ln_id_to_idx,
            "idx_to_ln_id": {str(k): v for k, v in self.idx_to_ln_id.items()},
            "next_idx": self.next_idx,
        }
        save_json(data, path)

    def load(self, path: str) -> None:
        """Load mapping from JSON file."""
        data = load_json(path)
        if data is None:
            logger.warning(f"Mapping file not found: {path}")
            return

        self.ln_id_to_idx = data.get("ln_id_to_idx", {})
        self.idx_to_ln_id = {int(k): v for k, v in data.get("idx_to_ln_id", {}).items()}
        self.next_idx = data.get("next_idx", len(self.ln_id_to_idx))

    def __len__(self) -> int:
        """Return number of mappings."""
        return len(self.ln_id_to_idx)
