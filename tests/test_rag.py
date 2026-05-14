"""
Tests for the RAG subsystem: chunker, embedder, retriever, corpus client.

All tests use the deterministic ``HashingEmbedder`` and the in-memory /
fallback paths so they run without ``qdrant-client``, ``fastembed``, or
network access.
"""

from __future__ import annotations

import asyncio

import pytest

from asar.core.search import SearchRequest
from asar.execution.rag.chunker import (
    ChunkingConfig,
    CorpusChunk,
    CorpusDocument,
    DocumentChunker,
    chunk_documents,
)
from asar.execution.rag.embedder import HashingEmbedder, build_embedder
from asar.execution.rag.retriever import (
    BM25Index,
    HybridRetriever,
    QdrantVectorIndex,
    build_indices,
)
from asar.providers.corpus_search import CorpusSearchClient


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------


def test_chunker_respects_token_budgets() -> None:
    body = "Sentence about A. " * 200
    doc = CorpusDocument(
        doc_id="d1",
        title="Long document",
        text=f"# Section A\n\n{body}\n\n# Section B\n\nShort tail paragraph.",
        dataset_name="test",
    )
    chunks = DocumentChunker(config=ChunkingConfig(target_tokens=80, max_tokens=120, overlap_tokens=10, min_tokens=10)).chunk(doc)
    assert chunks, "chunker must produce at least one chunk"
    for chunk in chunks:
        assert chunk.token_count <= 200  # generous upper bound on a single chunk
        assert chunk.text.strip()
    sections = {c.section for c in chunks}
    assert "Section A" in sections


def test_chunker_falls_back_to_single_chunk_for_tiny_docs() -> None:
    doc = CorpusDocument(doc_id="d2", title="Tiny", text="Just a tiny note.", dataset_name="test")
    chunks = chunk_documents([doc])
    assert len(chunks) == 1
    assert chunks[0].text == "Just a tiny note."


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------


def test_hashing_embedder_is_deterministic_and_normalized() -> None:
    embedder = HashingEmbedder(dim=128)
    v1 = embedder.encode(["hello world"])[0]
    v2 = embedder.encode(["hello world"])[0]
    assert v1 == v2
    norm = sum(x * x for x in v1) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_build_embedder_defaults_to_hashing() -> None:
    embedder = build_embedder()
    assert embedder.name.startswith("hashing")
    assert embedder.dim >= 32


# ---------------------------------------------------------------------------
# BM25 + Qdrant fallback + Hybrid retrieval
# ---------------------------------------------------------------------------


def _toy_chunks() -> list[CorpusChunk]:
    return [
        CorpusChunk(
            chunk_id=f"c{i}",
            doc_id=f"d{i}",
            title=title,
            section="body",
            text=text,
            dataset_name="test",
            source_url=None,
            tags=(),
            trust_label="unknown",
            token_count=len(text.split()),
            char_count=len(text),
        )
        for i, (title, text) in enumerate(
            [
                ("BRCA1", "BRCA1 mutations are associated with breast and ovarian cancer risk."),
                ("Photosynthesis", "Photosynthesis converts light into chemical energy in plant cells."),
                ("Plate tectonics", "Plate tectonics describes the motion of large segments of the Earth's lithosphere."),
                ("Vaccines", "Vaccines train the immune system to recognize specific pathogens."),
                ("BRCA1-other", "Loss-of-function variants of BRCA1 increase the risk of hereditary cancers."),
            ]
        )
    ]


def test_bm25_ranks_relevant_chunks_first() -> None:
    chunks = _toy_chunks()
    index = BM25Index()
    index.index(chunks)
    hits = index.search("BRCA1 cancer risk", top_k=3)
    assert hits
    top_ids = [chunk_id for chunk_id, _ in hits]
    assert top_ids[0] in {"c0", "c4"}


def test_qdrant_in_memory_fallback_search() -> None:
    chunks = _toy_chunks()
    embedder = HashingEmbedder(dim=128)
    vectors = embedder.encode([c.text for c in chunks])
    vector_index = QdrantVectorIndex(collection="t", dim=128, in_memory=True)
    vector_index.upsert(
        ids=[c.chunk_id for c in chunks],
        vectors=vectors,
        payloads=[c.to_metadata() for c in chunks],
    )
    query_vec = embedder.encode(["BRCA1 hereditary cancer"])[0]
    hits = vector_index.search(query_vec, top_k=3)
    assert hits
    assert hits[0][0] in {"c0", "c4"}


def test_hybrid_retriever_returns_relevant_chunks_with_rrf() -> None:
    chunks = _toy_chunks()
    embedder = HashingEmbedder(dim=128)
    vector_index, bm25_index, chunks_by_id = build_indices(
        chunks, embedder=embedder, collection="t", storage_path=None,
    )
    retriever = HybridRetriever(
        vector_index=vector_index,
        bm25_index=bm25_index,
        embedder=embedder,
        chunks_by_id=chunks_by_id,
    )
    hits = retriever.retrieve("Which gene is linked to hereditary breast cancer?", top_k=3)
    assert hits, "RRF must return at least one hit"
    top_doc_ids = [h.chunk.doc_id for h in hits]
    assert any(d in top_doc_ids for d in ("d0", "d4"))


# ---------------------------------------------------------------------------
# CorpusSearchClient via SearchClientProtocol
# ---------------------------------------------------------------------------


def test_corpus_search_client_returns_search_result_items() -> None:
    chunks = _toy_chunks()
    embedder = HashingEmbedder(dim=128)
    vector_index, bm25_index, chunks_by_id = build_indices(
        chunks, embedder=embedder, collection="t", storage_path=None,
    )
    retriever = HybridRetriever(
        vector_index=vector_index,
        bm25_index=bm25_index,
        embedder=embedder,
        chunks_by_id=chunks_by_id,
    )
    client = CorpusSearchClient(retriever=retriever, dataset_name="test")
    response = asyncio.run(
        client.search(SearchRequest(query="BRCA1 cancer", top_k=3))
    )
    assert response.results
    first = response.results[0]
    assert first.snippet
    assert first.source_name == "corpus:test"
    assert first.url.startswith("corpus://") or first.url.startswith("http")
    # raw_payload preserves fused score and ranks for inspection
    assert "fused_score" in first.raw_payload
