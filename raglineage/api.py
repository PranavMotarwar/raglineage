"""High-level API for RagLineage."""

import fnmatch
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from raglineage.audit.auditor import Auditor
from raglineage.config import RagLineageConfig
from raglineage.embedding.base import BaseEmbedder
from raglineage.embedding.local import LocalEmbedder
from raglineage.ingest.auto import AutoIngestor
from raglineage.lineage.diff import VersionDiff, compute_diff
from raglineage.lineage.graph import LineageGraph
from raglineage.lineage.versioning import VersionStore
from raglineage.retrieval.filters import FilterConfig
from raglineage.retrieval.retriever import Retriever
from raglineage.schemas.audit import AnswerWithLineage, LineageEntry, RetrievalHit
from raglineage.schemas.dataset import DatasetVersion
from raglineage.schemas.stats import RagLineageStats
from raglineage.schemas.lineage_node import LineageNode
from raglineage.store.base import BaseVectorStore
from raglineage.store.numpy_store import NumpyStore
from raglineage.transform.chunkers import SemanticChunkerTransform, SimpleChunkerTransform
from raglineage.transform.dedupe import DedupeTransform
from raglineage.transform.normalize import NormalizeTransform
from raglineage.utils.io import ensure_dir, load_json, save_json
from raglineage.utils.logging import get_logger

logger = get_logger(__name__)

try:
    from raglineage.embedding.openai import OpenAIEmbedder
except ImportError:
    OpenAIEmbedder = None  # type: ignore


class RagLineage:
    """High-level API for lineage-aware RAG."""

    def __init__(
        self,
        source: Path | str,
        store_backend: str | None = None,
        embed_backend: str | None = None,
        embed_model: str | None = None,
        chunk_size: int = 400,
        chunk_overlap: int = 80,
        chunking_strategy: str = "semantic",
        enable_dedupe: bool = True,
        enable_normalize: bool = True,
        normalize_aggressive: bool = False,
        graph_depth: int = 1,
    ) -> None:
        """
        Initialize RagLineage.

        Args:
            source: Source directory or file path
            store_backend: Vector store backend ("faiss")
            embed_backend: Embedding backend ("hash", "local", or "openai")
            embed_model: Embedding model name
            chunk_size: Chunk size for text splitting
            chunk_overlap: Overlap between chunks
            chunking_strategy: "simple" or "semantic"
            enable_dedupe: Enable deduplication
            enable_normalize: Enable normalization
            normalize_aggressive: Use aggressive normalization
            graph_depth: Graph walk depth for retrieval
        """
        self.source = Path(source)
        if not self.source.exists():
            raise FileNotFoundError(f"Source does not exist: {self.source}")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            adjusted_overlap = max(0, chunk_size // 5)
            logger.warning(
                f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size "
                f"({chunk_size}); using {adjusted_overlap}"
            )
            chunk_overlap = adjusted_overlap
        if graph_depth < 0:
            raise ValueError("graph_depth must be non-negative")

        # Keep state beside a single-file source, or inside a directory source.
        self.dataset_root = self.source if self.source.is_dir() else self.source.parent
        self.storage_dir = (
            self.source / ".raglineage"
            if self.source.is_dir()
            else self.source.parent / f".{self.source.name}.raglineage"
        )
        index_config_path = self.storage_dir / "index_config.json"
        persisted_config = load_json(index_config_path) if index_config_path.exists() else {}
        store_backend = store_backend or persisted_config.get("store_backend", "numpy")
        embed_backend = embed_backend or persisted_config.get("embed_backend", "hash")
        embed_model = embed_model or persisted_config.get(
            "embed_model", "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.config = RagLineageConfig(
            source=source,
            store_backend=store_backend,
            embed_backend=embed_backend,
            embed_model=embed_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy,
            enable_dedupe=enable_dedupe,
            enable_normalize=enable_normalize,
            normalize_aggressive=normalize_aggressive,
            graph_depth=graph_depth,
        )

        # Initialize components
        self.version_store = VersionStore(
            self.dataset_root, manifest_path=self.storage_dir / "manifest.json"
        )
        self.graph = LineageGraph()
        self.node_registry: dict[str, LineageNode] = {}
        self.embedder: BaseEmbedder | None = None
        self.store: BaseVectorStore | None = None
        self.retriever: Retriever | None = None
        self.auditor: Auditor | None = None

        ensure_dir(self.storage_dir)

    def _store_path(self) -> Path:
        """Return the canonical persistence path for the selected backend."""
        name = "numpy_index" if self.config.store_backend in ("numpy", "bruteforce") else "faiss_index"
        return self.storage_dir / name

    def _collect_source_files(self) -> list[Path]:
        """Collect user inputs while always excluding raglineage's own state."""
        if self.source.is_file():
            return [self.source]
        if not self.source.is_dir():
            return []
        return [
            path
            for path in self.source.rglob("*")
            if path.is_file() and self.storage_dir not in path.parents
        ]

    @classmethod
    def from_config(cls, path: Path | str) -> "RagLineage":
        """
        Create RagLineage from a YAML config file.

        Config keys: source (required), store_backend, embed_backend, embed_model,
        chunk_size, chunk_overlap, chunking_strategy, enable_dedupe, enable_normalize,
        normalize_aggressive, graph_depth. Path can be relative to config file.

        Example YAML:
          source: ./data
          embed_backend: local
          chunk_size: 400
          chunk_overlap: 80
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with path.open() as f:
            data = yaml.safe_load(f) or {}
        if "source" not in data:
            raise ValueError("Config must contain 'source'")
        # Resolve source relative to config file directory
        source = data["source"]
        if not Path(source).is_absolute():
            source = str(path.parent / source)
        kwargs = {
            "source": source,
            "store_backend": data.get("store_backend", "numpy"),
            "embed_backend": data.get("embed_backend", "hash"),
            "embed_model": data.get(
                "embed_model", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            "chunk_size": int(data.get("chunk_size", 400)),
            "chunk_overlap": int(data.get("chunk_overlap", 80)),
            "chunking_strategy": data.get("chunking_strategy", "semantic"),
            "enable_dedupe": bool(data.get("enable_dedupe", True)),
            "enable_normalize": bool(data.get("enable_normalize", True)),
            "normalize_aggressive": bool(data.get("normalize_aggressive", False)),
            "graph_depth": int(data.get("graph_depth", 1)),
        }
        return cls(**kwargs)

    def _initialize_embedder(self) -> BaseEmbedder:
        """Initialize embedding backend."""
        if self.embedder is not None:
            return self.embedder

        if self.config.embed_backend == "hash":
            self.embedder = LocalEmbedder("hash")
        elif self.config.embed_backend == "local":
            self.embedder = LocalEmbedder(self.config.embed_model)
        elif self.config.embed_backend == "openai":
            if OpenAIEmbedder is None:
                raise ImportError("OpenAI embedder not available. Install with: pip install raglineage[openai]")
            self.embedder = OpenAIEmbedder(self.config.embed_model)
        else:
            raise ValueError(
                f"Unknown embed backend: {self.config.embed_backend}. "
                "Expected hash, local, or openai."
            )

        return self.embedder

    def _initialize_store(self, load_existing: bool = True) -> BaseVectorStore:
        """Initialize vector store."""
        if self.store is not None:
            return self.store

        embedder = self._initialize_embedder()
        dimension = embedder.dimension

        if self.config.store_backend == "faiss":
            store_path = self._store_path()
            # Import lazily so raglineage can work without FAISS installed.
            try:
                from raglineage.store.faiss_store import FAISSStore
            except ImportError as exc:
                raise ImportError(
                    "FAISS backend requires: pip install 'raglineage[faiss]'"
                ) from exc

            self.store = FAISSStore(dimension)
            if load_existing and store_path.exists():
                self.store.load(str(store_path))
        elif self.config.store_backend in ("numpy", "bruteforce"):
            store_path = self._store_path()
            self.store = NumpyStore(dimension)
            if load_existing and store_path.with_suffix(".npy").exists():
                self.store.load(str(store_path))
        else:
            raise ValueError(f"Unknown store backend: {self.config.store_backend}")

        return self.store

    def _load_graph(self) -> None:
        """Load lineage graph from disk."""
        graph_path = self.storage_dir / "graph.json"
        if graph_path.exists():
            data = load_json(graph_path)
            if data:
                self.graph.load_json(data, self.node_registry)

    def _save_graph(self) -> None:
        """Save lineage graph to disk."""
        graph_path = self.storage_dir / "graph.json"
        save_json(self.graph.export_json(), graph_path)

    def build(
        self,
        version: str = "v1.0",
        exclude: Optional[list[str]] = None,
        _allow_empty: bool = False,
    ) -> None:
        """
        Build RAG database from source.

        Args:
            version: Dataset version tag
            exclude: Optional list of glob patterns to exclude (e.g. ["*.log", ".git/*", "__pycache__"])
        """
        logger.info(f"Building RAG database version {version} from {self.source}")

        # A build is a clean snapshot. Never merge with vectors left by an
        # earlier build, which can otherwise surface stale or unregistered IDs.
        self.graph = LineageGraph()
        self.node_registry = {}
        self.store = None
        self.retriever = None
        self.auditor = None

        # Initialize components
        embedder = self._initialize_embedder()
        store = self._initialize_store(load_existing=False)

        # Collect source files
        source_files = self._collect_source_files()

        # Apply exclude patterns (glob-style: *.log, .git, __pycache__, etc.)
        if exclude:
            filtered = []
            for f in source_files:
                rel = str(f.relative_to(self.dataset_root)).replace("\\", "/")
                skip = False
                for p in exclude:
                    p_ = p.rstrip("/")
                    if fnmatch.fnmatch(rel, p) or rel == p_ or rel.startswith(p_ + "/"):
                        skip = True
                        break
                if not skip:
                    filtered.append(f)
            source_files = filtered

        ingestor = AutoIngestor(dataset_version=version)
        source_files = [path for path in source_files if ingestor.can_ingest(path)]
        if not source_files and not _allow_empty:
            raise ValueError(
                "No ingestible content found. Supported formats: .txt, .text, "
                ".md, .markdown, .rst, .csv, and .json"
            )

        # Create version
        relative_files = [f.relative_to(self.dataset_root) for f in source_files]
        self.version_store.create_version(
            version, relative_files, metadata={"exclude": exclude or []}
        )

        # Initialize transforms
        if self.config.chunking_strategy == "semantic":
            chunker = SemanticChunkerTransform(self.config.chunk_size, self.config.chunk_overlap)
        else:
            chunker = SimpleChunkerTransform(self.config.chunk_size, self.config.chunk_overlap)

        dedupe = DedupeTransform() if self.config.enable_dedupe else None
        normalize = (
            NormalizeTransform(aggressive=self.config.normalize_aggressive)
            if self.config.enable_normalize
            else None
        )

        # Ingest and transform
        all_nodes: list[LineageNode] = []

        for source_file in source_files:
            logger.info(f"Ingesting: {source_file}")
            for ln in ingestor.ingest(source_file):
                # Apply transforms
                current_nodes = [ln]
                for transform in [chunker, normalize, dedupe]:
                    if transform is None:
                        continue
                    new_nodes = []
                    for node in current_nodes:
                        new_nodes.extend(transform.transform(node))
                    current_nodes = new_nodes

                all_nodes.extend(current_nodes)

        if not all_nodes and not _allow_empty:
            raise ValueError("Source files contained no ingestible, non-empty records")

        # Add to graph and store
        logger.info(f"Adding {len(all_nodes)} nodes to graph and store")
        embeddings_batch = (
            embedder.embed_batch([node.content for node in all_nodes]) if all_nodes else []
        )

        for node, embedding in zip(all_nodes, embeddings_batch):
            self.node_registry[node.ln_id] = node
            self.graph.add_node(node)
            store.add(node.ln_id, embedding)

            # Add graph edges (adjacent chunks)
            if "_chunk_" in node.ln_id:
                base_id = node.ln_id.rsplit("_chunk_", 1)[0]
                chunk_idx = int(node.ln_id.rsplit("_", 1)[1])
                if chunk_idx > 0:
                    prev_chunk_id = f"{base_id}_chunk_{chunk_idx - 1}"
                    if prev_chunk_id in self.node_registry:
                        self.graph.add_edge(prev_chunk_id, node.ln_id, edge_type="adjacent")

        # Save
        store.save(str(self._store_path()))
        self._save_graph()
        save_json(
            {
                "store_backend": self.config.store_backend,
                "embed_backend": self.config.embed_backend,
                "embed_model": self.config.embed_model,
                "dimension": embedder.dimension,
            },
            self.storage_dir / "index_config.json",
        )
        logger.info(f"Build complete: {len(all_nodes)} nodes, version {version}")

    def update(
        self,
        version: str,
        changed_only: bool = True,
        exclude: list[str] | None = None,
    ) -> None:
        """
        Update to a new, internally consistent dataset snapshot.

        Args:
            version: New version tag
            changed_only: Retained for API compatibility. Change detection is
                reported, while the index is rebuilt to guarantee a complete
                single-version snapshot.
            exclude: Exclude patterns. When omitted, reuse the previous
                version's build exclusions.
        """
        current_version = self.version_store.get_current_version()
        if current_version is None:
            logger.warning("No current version found, doing full build")
            self.build(version)
            return

        version_from = self.version_store.get_version(current_version)
        if version_from is None:
            logger.warning("Current version not found, doing full build")
            self.build(version)
            return

        effective_exclude = (
            exclude if exclude is not None else list(version_from.metadata.get("exclude", []))
        )
        current_files = [
            path.relative_to(self.dataset_root)
            for path in self._collect_source_files()
            if AutoIngestor(version).can_ingest(path)
            and not any(
                fnmatch.fnmatch(
                    str(path.relative_to(self.dataset_root)).replace("\\", "/"), pattern
                )
                for pattern in effective_exclude
            )
        ]
        preview = DatasetVersion(
            version=version,
            created_at=datetime.now(timezone.utc),
            files=self.version_store.build_file_entries(current_files),
        )
        changes = compute_diff(version_from, preview)
        logger.info(f"Changed files: {len(changes.get_changed_files())}")
        self.build(version, exclude=effective_exclude, _allow_empty=True)
        logger.info(f"Update complete: version {version}")

    def query(
        self, question: str, k: int = 5, filters: FilterConfig | None = None
    ) -> AnswerWithLineage:
        """
        Query the RAG database.

        Args:
            question: Query question
            k: Number of results
            filters: Optional filters

        Returns:
            Answer with lineage
        """
        if self.retriever is None:
            embedder = self._initialize_embedder()
            store = self._initialize_store()
            self._load_graph()
            self.retriever = Retriever(embedder, store, self.graph, self.node_registry)

        results = self.retriever.retrieve(
            question, k=k, filters=filters, graph_depth=self.config.graph_depth
        )

        # Core raglineage is provider-neutral: return the best passage as an
        # extractive answer. Applications that need synthesis should use
        # retrieve() + format_context_for_llm() with their chosen LLM.
        answer_text = "No relevant information found."
        if results:
            answer_text = self.node_registry[results[0][0]].content

        # Build lineage entries
        lineage_entries = []
        for ln_id, score in results:
            if ln_id in self.node_registry:
                ln = self.node_registry[ln_id]
                lineage_entries.append(
                    LineageEntry(
                        ln_id=ln.ln_id,
                        score=score,
                        source=ln.source,
                        dataset_version=ln.dataset_version,
                        transform_chain=ln.transform_chain,
                    )
                )

        return AnswerWithLineage(
            question=question,
            answer=answer_text,
            lineage=lineage_entries,
            metadata={"answer_mode": "extractive", "retrieved_count": len(results)},
        )

    def retrieve(
        self, question: str, k: int = 5, filters: FilterConfig | None = None
    ) -> list[RetrievalHit]:
        """
        Retrieve chunks with lineage only (no generated answer). Use with your own LLM.

        Returns list of RetrievalHit with content, score, and source. Build your own
        context string or prompt from hit.content and pass to any LLM.

        Args:
            question: Query question
            k: Number of results
            filters: Optional filters

        Returns:
            List of RetrievalHit (content, score, source, version, etc.)
        """
        if self.retriever is None:
            embedder = self._initialize_embedder()
            store = self._initialize_store()
            self._load_graph()
            self.retriever = Retriever(embedder, store, self.graph, self.node_registry)

        results = self.retriever.retrieve(
            question, k=k, filters=filters, graph_depth=self.config.graph_depth
        )

        hits = []
        for ln_id, score in results:
            if ln_id not in self.node_registry:
                continue
            ln = self.node_registry[ln_id]
            hits.append(
                RetrievalHit(
                    content=ln.content,
                    score=score,
                    ln_id=ln.ln_id,
                    source=ln.source,
                    dataset_version=ln.dataset_version,
                    transform_chain=ln.transform_chain,
                )
            )
        return hits

    @staticmethod
    def format_context_for_llm(
        hits: list[RetrievalHit],
        include_sources: bool = True,
        separator: str = "\n\n",
        max_content_chars: Optional[int] = None,
    ) -> str:
        """
        Format retrieval hits into a single context string for LLM prompts.

        Example: context = RagLineage.format_context_for_llm(rag.retrieve("...", k=5))
        Then pass context to your LLM. Also available as RetrievalHit.format_context_for_llm(hits).
        """
        return RetrievalHit.format_context_for_llm(
            hits,
            include_sources=include_sources,
            separator=separator,
            max_content_chars=max_content_chars,
        )

    def audit(self, answer: AnswerWithLineage) -> Any:
        """
        Audit an answer.

        Args:
            answer: Answer with lineage

        Returns:
            Audit report
        """
        if self.auditor is None:
            current_version = self.version_store.get_current_version()
            self.auditor = Auditor(current_version)

        return self.auditor.audit(answer)

    def stats(self) -> RagLineageStats:
        """
        Get dataset statistics without loading the full store.

        Returns:
            RagLineageStats with node count, version info, and build status
        """
        storage_path = self.storage_dir
        store_path = self._store_path()
        is_built = store_path.exists() or store_path.with_suffix(".npy").exists()

        node_count = 0
        if is_built:
            graph_data = load_json(storage_path / "graph.json")
            if graph_data and "nodes" in graph_data:
                node_count = len(graph_data["nodes"])

        manifest = self.version_store.load_manifest()
        current_version = None
        source_files = 0
        versions: list[str] = []

        if manifest:
            current_version = manifest.current_version
            versions = [v.version for v in manifest.versions]
            if current_version:
                version_obj = manifest.get_version(current_version)
                if version_obj:
                    source_files = len(version_obj.files)

        return RagLineageStats(
            node_count=node_count,
            current_version=current_version,
            source_files=source_files,
            versions=versions,
            storage_path=str(storage_path),
            is_built=is_built,
        )

    def batch_query(
        self, questions: list[str], k: int = 5, filters: FilterConfig | None = None
    ) -> list[AnswerWithLineage]:
        """
        Query multiple questions at once. Useful for batch processing.

        Args:
            questions: List of query questions
            k: Number of results per question
            filters: Optional filters

        Returns:
            List of AnswerWithLineage, one per question
        """
        return [self.query(q, k=k, filters=filters) for q in questions]

    def diff(self, version_from: str, version_to: str) -> VersionDiff:
        """
        Diff two dataset versions.

        Args:
            version_from: Source version
            version_to: Target version

        Returns:
            VersionDiff object
        """
        from_version = self.version_store.get_version(version_from)
        to_version = self.version_store.get_version(version_to)

        if from_version is None:
            raise ValueError(f"Version not found: {version_from}")
        if to_version is None:
            raise ValueError(f"Version not found: {version_to}")

        from raglineage.lineage.diff import compute_diff

        return compute_diff(from_version, to_version)
