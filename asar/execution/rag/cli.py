"""
Reproducibly download and index a RAG corpus.

Usage:
    uv run python -m asar.execution.rag.cli \\
        --dataset scifact \\
        --embed-backend hashing|fastembed \\
        --root data/corpora/scifact

Writes:
    <root>/raw/corpus.jsonl.gz
    <root>/normalized/documents.jsonl
    <root>/normalized/chunks.jsonl
    <root>/index/qdrant/  (when persistent storage is requested)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from asar.execution.rag.chunker import ChunkingConfig, DocumentChunker
from asar.execution.rag.embedder import build_embedder
from asar.execution.rag.retriever import build_indices, dump_chunks
from asar.execution.rag.scifact_loader import SciFactDatasetAdapter, default_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a RAG corpus index for ASAR.")
    parser.add_argument("--dataset", default="scifact", choices=["scifact"])
    parser.add_argument("--embed-backend", default="hashing", choices=["hashing", "fastembed"])
    parser.add_argument("--root", default=None, help="Storage root. Defaults to data/corpora/<dataset>.")
    parser.add_argument("--no-download", action="store_true", help="Skip download (use pre-staged raw files).")
    parser.add_argument("--target-tokens", type=int, default=450)
    parser.add_argument("--max-tokens", type=int, default=650)
    parser.add_argument("--overlap-tokens", type=int, default=80)
    parser.add_argument("--min-tokens", type=int, default=120)
    parser.add_argument("--probe-query", default="What causes BRCA1-related cancers?")
    args = parser.parse_args(argv)

    if args.dataset != "scifact":  # pragma: no cover
        print(f"Unsupported dataset: {args.dataset}", file=sys.stderr)
        return 2

    root = Path(args.root) if args.root else default_root()
    adapter = SciFactDatasetAdapter(root=root)

    t0 = time.perf_counter()
    print(f"[1/4] Preparing {args.dataset} under {root} (download={not args.no_download}) ...")
    adapter.prepare(download=not args.no_download)
    docs = list(adapter.documents())
    print(f"      normalized documents: {len(docs)}")

    t1 = time.perf_counter()
    print(f"[2/4] Chunking ...")
    chunker = DocumentChunker(
        config=ChunkingConfig(
            target_tokens=args.target_tokens,
            max_tokens=args.max_tokens,
            overlap_tokens=args.overlap_tokens,
            min_tokens=args.min_tokens,
        )
    )
    chunks = [chunk for doc in docs for chunk in chunker.chunk(doc)]
    dump_chunks(chunks, adapter.paths.normalized / "chunks.jsonl")
    print(f"      chunks produced: {len(chunks)}")

    t2 = time.perf_counter()
    print(f"[3/4] Embedding & indexing (backend={args.embed_backend}) ...")
    embedder = build_embedder(args.embed_backend)
    storage_path = adapter.paths.index / "qdrant"
    vector_index, bm25_index, chunks_by_id = build_indices(
        chunks,
        embedder=embedder,
        collection="asar_scifact_chunks",
        storage_path=storage_path,
    )
    t3 = time.perf_counter()
    print(f"      embedded dim={embedder.dim} name={embedder.name}")
    print(f"      vector index at: {storage_path}")

    print(f"[4/4] Probe retrieval: {args.probe_query!r}")
    from asar.execution.rag.retriever import HybridRetriever

    retriever = HybridRetriever(
        vector_index=vector_index,
        bm25_index=bm25_index,
        embedder=embedder,
        chunks_by_id=chunks_by_id,
    )
    hits = retriever.retrieve(args.probe_query, top_k=5)
    for rank, hit in enumerate(hits, start=1):
        snippet = hit.chunk.text.replace("\n", " ")[:160]
        print(f"      {rank}. score={hit.score:.4f} doc={hit.chunk.doc_id} :: {snippet}...")

    t4 = time.perf_counter()
    print("--")
    print(f"prepare:   {t1 - t0:6.2f}s")
    print(f"chunk:     {t2 - t1:6.2f}s")
    print(f"index:     {t3 - t2:6.2f}s")
    print(f"retrieval: {t4 - t3:6.2f}s")
    print(f"total:     {t4 - t0:6.2f}s")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
