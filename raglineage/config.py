from typing import Union
"""Configuration dataclasses."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class RagLineageConfig:
    """Configuration for RagLineage."""

    source: Union[Path, str]
    store_backend: Literal["faiss", "numpy", "bruteforce"] = "numpy"
    embed_backend: Literal["hash", "local", "openai"] = "hash"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 400
    chunk_overlap: int = 80
    chunking_strategy: Literal["simple", "semantic"] = "semantic"
    enable_dedupe: bool = True
    enable_normalize: bool = True
    normalize_aggressive: bool = False
    graph_depth: int = 1
