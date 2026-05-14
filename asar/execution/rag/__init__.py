"""
RAG subsystem — corpus-backed retrieval that plugs into the existing
execution/search boundary via `SearchClientProtocol`.

Public surface:
- `CorpusDocument`, `CorpusChunk` — normalized corpus types
- `DocumentChunker` — section/paragraph/sentence-aware chunking with overlap
- `EmbedderProtocol`, `FastEmbedEmbedder`, `HashingEmbedder` — embedding backends
- `QdrantVectorIndex` — local Qdrant index over chunks
- `BM25Index` — in-memory lexical index over chunks
- `HybridRetriever` — dense + BM25 with reciprocal-rank fusion
- `CorpusSearchClient` — `SearchClientProtocol` adapter so the existing
  `WebSearchExecutor` can transparently use the corpus instead of the web
"""

from __future__ import annotations

from asar.execution.rag.chunker import CorpusChunk, CorpusDocument, DocumentChunker
from asar.execution.rag.embedder import (
    EmbedderProtocol,
    FastEmbedEmbedder,
    HashingEmbedder,
    build_embedder,
)
from asar.execution.rag.retriever import BM25Index, HybridRetriever, QdrantVectorIndex
from asar.execution.rag.scifact_loader import SciFactDatasetAdapter

__all__ = [
    "BM25Index",
    "CorpusChunk",
    "CorpusDocument",
    "DocumentChunker",
    "EmbedderProtocol",
    "FastEmbedEmbedder",
    "HashingEmbedder",
    "HybridRetriever",
    "QdrantVectorIndex",
    "SciFactDatasetAdapter",
    "build_embedder",
]
