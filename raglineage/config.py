"""Configuration dataclasses."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class RagLineageConfig:
    """Configuration for RagLineage."""

    source: Union[Path, str]
    store_backend: Literal["faiss"] = "faiss"
    embed_backend: Literal["local", "openai"] = "local"
    embed_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: Literal["simple", "semantic"] = "semantic"
    enable_dedupe: bool = True
    enable_normalize: bool = True
    normalize_aggressive: bool = False
    graph_depth: int = 1
