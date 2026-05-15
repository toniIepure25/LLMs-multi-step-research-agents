"""
Corpus-backed `SearchClientProtocol` adapter.

This is the single integration seam between the new RAG subsystem and the
existing ASAR execution layer. By implementing `SearchClientProtocol`, the
existing `WebSearchExecutor` can call this adapter exactly the same way it
calls Tavily/Brave — and the existing normalization into `EvidenceItem`
applies unchanged downstream.
"""

from __future__ import annotations

import os
from pathlib import Path

from asar.core.errors import SearchClientError
from asar.core.search import SearchRequest, SearchResponse, SearchResultItem
from asar.execution.rag.chunker import (
    ChunkingConfig,
    CorpusChunk,
    DocumentChunker,
)
from asar.execution.rag.embedder import EmbedderProtocol, build_embedder
from asar.execution.rag.retriever import (
    HybridRetriever,
    build_indices,
)
from asar.execution.rag.scifact_loader import SciFactDatasetAdapter, default_root


_DEFAULT_COLLECTION = "asar_scifact_chunks"


class CorpusSearchClient:
    """Local corpus retriever exposed as a `SearchClientProtocol`.

    Lifecycle:
    1. Build or load chunks from the configured dataset.
    2. Embed chunks once at construction time (or load a persisted index).
    3. On each ``search`` call, run hybrid retrieval and return
       ``SearchResultItem`` records that look exactly like web-search results
       to the existing executor.
    """

    def __init__(
        self,
        *,
        retriever: HybridRetriever,
        dataset_name: str,
    ) -> None:
        self._retriever = retriever
        self._dataset_name = dataset_name

    async def search(self, request: SearchRequest) -> SearchResponse:
        try:
            hits = self._retriever.retrieve(request.query, top_k=request.top_k)
        except Exception as exc:  # pragma: no cover - defensive
            raise SearchClientError(
                "Corpus retrieval failed",
                details={"query": request.query, "error": str(exc)},
                retryable=False,
            ) from exc

        # RRF fused scores live in a tiny absolute range (≤ ~0.033 with k=60).
        # We expose them as a 0..1 *relative* relevance gauge per response so
        # the top hit reads ~100% and the rest scale proportionally.  The raw
        # fused score is still surfaced in ``raw_payload`` for debugging.
        max_raw = max((h.score for h in hits), default=0.0)

        results: list[SearchResultItem] = []
        for rank, hit in enumerate(hits, start=1):
            chunk = hit.chunk
            results.append(
                SearchResultItem(
                    url=chunk.source_url or f"corpus://{self._dataset_name}/{chunk.doc_id}",
                    snippet=chunk.text,
                    title=chunk.title or f"{self._dataset_name} document {chunk.doc_id}",
                    publication_date=None,
                    rank=rank,
                    score=_to_unit_score(hit.score, max_raw=max_raw),
                    source_name=f"corpus:{self._dataset_name}",
                    raw_payload={
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.doc_id,
                        "section": chunk.section,
                        "tags": list(chunk.tags),
                        "trust_label": chunk.trust_label,
                        "dense_rank": hit.dense_rank,
                        "lexical_rank": hit.lexical_rank,
                        "fused_score": hit.score,
                    },
                )
            )
        return SearchResponse(results=results)


def _to_unit_score(raw_score: float, *, max_raw: float) -> float:
    """Map a raw RRF fused score to a 0..1 relevance gauge.

    Strategy: normalize against the maximum fused score in this response so
    the top hit reads ~1.0 and weaker hits scale proportionally.  A small
    floor (0.05) keeps zero/near-zero scores visible on the UI gauge.
    """
    if raw_score <= 0.0:
        return 0.0
    if max_raw <= 0.0:
        return 0.0
    return min(1.0, max(0.05, raw_score / max_raw))


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_corpus_search_client(
    *,
    dataset: str | None = None,
    embedder_backend: str | None = None,
    chunking: ChunkingConfig | None = None,
    storage_root: str | Path | None = None,
    download: bool = True,
) -> CorpusSearchClient:
    """Construct a ready-to-use corpus search client.

    The dataset defaults to ``scifact`` (the documented first integration).
    The embedder defaults to the hashing fallback so the client works with no
    network or heavy dependency; set ``ASAR_RAG_EMBED_BACKEND=fastembed`` for
    real semantic embeddings.
    """
    name = (dataset or os.environ.get("ASAR_CORPUS_DATASET") or "scifact").strip().lower()
    if name != "scifact":
        raise ValueError(f"Unsupported corpus dataset: {name!r}. Only 'scifact' is wired in v1.")
    root = Path(storage_root) if storage_root else default_root()
    adapter = SciFactDatasetAdapter(root=root)
    adapter.prepare(download=download)

    docs = list(adapter.documents())
    if not docs:
        raise RuntimeError(
            "SciFact corpus is empty after preparation — check downloads under "
            f"{root}/raw/"
        )

    chunker = DocumentChunker(config=chunking or ChunkingConfig())
    chunks: list[CorpusChunk] = []
    for doc in docs:
        chunks.extend(chunker.chunk(doc))
    if not chunks:
        raise RuntimeError("SciFact chunking produced zero chunks")

    embedder: EmbedderProtocol = build_embedder(embedder_backend)
    storage_path = adapter.paths.index / "qdrant"

    vector_index, bm25_index, chunks_by_id = build_indices(
        chunks,
        embedder=embedder,
        collection=_DEFAULT_COLLECTION,
        storage_path=storage_path,
    )

    retriever = HybridRetriever(
        vector_index=vector_index,
        bm25_index=bm25_index,
        embedder=embedder,
        chunks_by_id=chunks_by_id,
    )
    return CorpusSearchClient(retriever=retriever, dataset_name=name)
