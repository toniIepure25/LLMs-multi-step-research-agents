"""
Hybrid retriever: dense vector search (Qdrant) + lexical search (BM25) + RRF.

Design goals:
- Each component is independently usable and testable.
- ``QdrantVectorIndex`` works with either an in-memory or on-disk Qdrant store.
- ``BM25Index`` keeps an in-memory token map so it runs anywhere.
- ``HybridRetriever`` fuses both rankings with reciprocal-rank fusion.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from asar.execution.rag.chunker import CorpusChunk
from asar.execution.rag.embedder import EmbedderProtocol


_WORD_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass
class RetrievalHit:
    """One retrieved chunk with a fused score."""

    chunk: CorpusChunk
    score: float
    dense_rank: int | None = None
    lexical_rank: int | None = None


# ---------------------------------------------------------------------------
# Qdrant vector index
# ---------------------------------------------------------------------------


class QdrantVectorIndex:
    """Thin Qdrant adapter restricted to what RAG actually needs.

    Falls back to an in-process numpy-less brute-force index when
    ``qdrant-client`` is not installed — useful for smoke tests.
    """

    def __init__(
        self,
        *,
        collection: str,
        dim: int,
        storage_path: str | Path | None = None,
        in_memory: bool = False,
    ) -> None:
        self._collection = collection
        self._dim = dim
        self._storage_path = Path(storage_path) if storage_path else None
        self._in_memory = in_memory or storage_path is None
        self._client = None
        self._distance = None
        self._fallback: list[tuple[str, list[float], dict]] = []
        self._using_fallback = False
        self._connect()

    def _connect(self) -> None:
        try:
            from qdrant_client import QdrantClient  # type: ignore
            from qdrant_client.http.models import Distance, VectorParams  # type: ignore
        except ImportError:
            self._using_fallback = True
            return

        if self._storage_path is not None:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(self._storage_path))
        else:
            self._client = QdrantClient(":memory:")
        self._distance = Distance.COSINE
        # Create collection if missing.
        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
            )

    def upsert(self, ids: list[str], vectors: list[list[float]], payloads: list[dict]) -> None:
        if len(ids) != len(vectors) or len(ids) != len(payloads):
            raise ValueError("ids, vectors, payloads must have the same length")
        if self._using_fallback or self._client is None:
            self._fallback = [
                (i, v, p) for i, v, p in zip(ids, vectors, payloads, strict=True)
            ]
            return
        from qdrant_client.http.models import PointStruct  # type: ignore

        points = [
            PointStruct(id=_id_to_int(point_id), vector=vec, payload={**payload, "chunk_uid": point_id})
            for point_id, vec, payload in zip(ids, vectors, payloads, strict=True)
        ]
        # Upsert in modest batches to avoid huge single requests.
        batch = 256
        for i in range(0, len(points), batch):
            self._client.upsert(collection_name=self._collection, points=points[i : i + batch])

    def search(self, vector: list[float], top_k: int) -> list[tuple[str, float, dict]]:
        if self._using_fallback or self._client is None:
            return _brute_force_search(self._fallback, vector, top_k)
        # Prefer the modern query_points API; fall back to legacy search if
        # the installed qdrant-client version is older.
        if hasattr(self._client, "query_points"):
            response = self._client.query_points(
                collection_name=self._collection,
                query=vector,
                limit=top_k,
                with_payload=True,
            )
            points = getattr(response, "points", response)
        else:
            points = self._client.search(  # type: ignore[attr-defined]
                collection_name=self._collection,
                query_vector=vector,
                limit=top_k,
                with_payload=True,
            )
        out: list[tuple[str, float, dict]] = []
        for r in points:
            payload = r.payload or {}
            chunk_uid = str(payload.get("chunk_uid") or r.id)
            out.append((chunk_uid, float(r.score), payload))
        return out


def _id_to_int(point_id: str) -> int:
    """Qdrant prefers integer or UUID ids; we hash the chunk uid into an int."""
    import hashlib

    digest = hashlib.blake2b(point_id.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") & 0x7FFFFFFFFFFFFFFF


def _brute_force_search(
    rows: list[tuple[str, list[float], dict]],
    query: list[float],
    top_k: int,
) -> list[tuple[str, float, dict]]:
    if not rows:
        return []
    qnorm = math.sqrt(sum(x * x for x in query)) or 1.0
    scored: list[tuple[float, str, dict]] = []
    for _id, vec, payload in rows:
        vnorm = math.sqrt(sum(x * x for x in vec)) or 1.0
        dot = sum(a * b for a, b in zip(query, vec, strict=True))
        scored.append((dot / (qnorm * vnorm), _id, payload))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [(point_id, score, payload) for score, point_id, payload in scored[:top_k]]


# ---------------------------------------------------------------------------
# BM25 lexical index
# ---------------------------------------------------------------------------


class BM25Index:
    """Minimal Okapi BM25 over chunk text.

    Uses ``rank_bm25`` when available, falls back to a small hand-rolled BM25
    implementation otherwise. Both give the same ranking on toy corpora.
    """

    def __init__(self, *, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._chunks: list[CorpusChunk] = []
        self._tokens: list[list[str]] = []
        self._bm25 = None

    def index(self, chunks: Iterable[CorpusChunk]) -> None:
        self._chunks = list(chunks)
        self._tokens = [_tokenize(c.text) for c in self._chunks]
        try:
            from rank_bm25 import BM25Okapi  # type: ignore
        except ImportError:
            self._bm25 = None
            return
        self._bm25 = BM25Okapi(self._tokens, k1=self._k1, b=self._b)

    def search(self, query: str, top_k: int) -> list[tuple[str, float]]:
        if not self._chunks:
            return []
        q_tokens = _tokenize(query)
        if self._bm25 is not None:
            scores = self._bm25.get_scores(q_tokens)
        else:
            scores = self._fallback_scores(q_tokens)
        ranked = sorted(
            enumerate(scores), key=lambda pair: pair[1], reverse=True
        )[:top_k]
        return [
            (self._chunks[idx].chunk_id, float(score))
            for idx, score in ranked
            if score > 0.0
        ]

    # -- internals -------------------------------------------------------

    def _fallback_scores(self, query_tokens: list[str]) -> list[float]:
        # Hand-rolled BM25 — used only when rank_bm25 is unavailable.
        n_docs = len(self._tokens)
        if n_docs == 0:
            return []
        avgdl = sum(len(toks) for toks in self._tokens) / n_docs or 1.0
        # document frequency for each query term
        df: dict[str, int] = {}
        for token in set(query_tokens):
            df[token] = sum(1 for toks in self._tokens if token in toks)
        scores = [0.0] * n_docs
        for i, toks in enumerate(self._tokens):
            doc_len = len(toks) or 1
            tf: dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            for token in query_tokens:
                if df.get(token, 0) == 0:
                    continue
                idf = math.log(((n_docs - df[token] + 0.5) / (df[token] + 0.5)) + 1)
                term_tf = tf.get(token, 0)
                if term_tf == 0:
                    continue
                numer = term_tf * (self._k1 + 1)
                denom = term_tf + self._k1 * (1 - self._b + self._b * doc_len / avgdl)
                scores[i] += idf * numer / denom
        return scores


def _tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(text or "")]


# ---------------------------------------------------------------------------
# Hybrid retriever (RRF)
# ---------------------------------------------------------------------------


class HybridRetriever:
    """Reciprocal-rank fusion over a dense and a lexical retriever."""

    def __init__(
        self,
        *,
        vector_index: QdrantVectorIndex,
        bm25_index: BM25Index,
        embedder: EmbedderProtocol,
        chunks_by_id: dict[str, CorpusChunk],
        rrf_k: int = 60,
    ) -> None:
        self._vector_index = vector_index
        self._bm25_index = bm25_index
        self._embedder = embedder
        self._chunks_by_id = chunks_by_id
        self._rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        if not query.strip():
            return []
        # Dense
        query_vec = self._embedder.encode([query])[0]
        dense_results = self._vector_index.search(query_vec, top_k=top_k * 4)
        # Lexical
        lexical_results = self._bm25_index.search(query, top_k=top_k * 4)

        scores: dict[str, float] = {}
        dense_ranks: dict[str, int] = {}
        lexical_ranks: dict[str, int] = {}
        for rank, (chunk_id, _score, _payload) in enumerate(dense_results, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (self._rrf_k + rank)
            dense_ranks[chunk_id] = rank
        for rank, (chunk_id, _score) in enumerate(lexical_results, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (self._rrf_k + rank)
            lexical_ranks[chunk_id] = rank

        fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        hits: list[RetrievalHit] = []
        for chunk_id, fused_score in fused:
            chunk = self._chunks_by_id.get(chunk_id)
            if chunk is None:
                continue
            hits.append(
                RetrievalHit(
                    chunk=chunk,
                    score=fused_score,
                    dense_rank=dense_ranks.get(chunk_id),
                    lexical_rank=lexical_ranks.get(chunk_id),
                )
            )
        return hits


# ---------------------------------------------------------------------------
# Index building helper
# ---------------------------------------------------------------------------


def build_indices(
    chunks: list[CorpusChunk],
    *,
    embedder: EmbedderProtocol,
    collection: str,
    storage_path: str | Path | None = None,
) -> tuple[QdrantVectorIndex, BM25Index, dict[str, CorpusChunk]]:
    """Build dense + lexical indices over the given chunks."""
    vector_index = QdrantVectorIndex(
        collection=collection,
        dim=embedder.dim,
        storage_path=storage_path,
        in_memory=storage_path is None,
    )
    bm25_index = BM25Index()

    texts = [c.text for c in chunks]
    vectors = embedder.encode(texts)
    ids = [c.chunk_id for c in chunks]
    payloads = [c.to_metadata() for c in chunks]

    vector_index.upsert(ids=ids, vectors=vectors, payloads=payloads)
    bm25_index.index(chunks)
    chunks_by_id = {c.chunk_id: c for c in chunks}
    return vector_index, bm25_index, chunks_by_id


def dump_chunks(chunks: list[CorpusChunk], path: Path) -> None:
    """Persist chunks to JSONL for inspection or rebuilds."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for chunk in chunks:
            fh.write(json.dumps(chunk.to_metadata()) + "\n")
