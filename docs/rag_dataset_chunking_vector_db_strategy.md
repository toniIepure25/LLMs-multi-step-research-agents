# Corpus-Backed RAG Integration Strategy

This document records the first real corpus-backed RAG subsystem added to ASAR.
It is intentionally small and production-oriented: one dataset, one vector DB,
one hybrid retrieval path, and one clean integration seam back into the existing
execution → evidence pipeline.

## Scope

This first version covers:

- dataset selection under the 2GB download limit
- reproducible local download and normalization
- document-aware chunking
- vector indexing in Qdrant
- hybrid dense + lexical retrieval
- normalization back into the existing `EvidenceItem` flow

This first version does **not** redesign orchestration, add a new top-level RAG
layer, or change downstream schemas.

## Where It Fits In The Current Architecture

The new subsystem stays inside the existing execution/search boundary:

`TaskPacket -> SearchClientProtocol -> WebSearchExecutor -> EvidenceItem`

Instead of bypassing execution, the new code adds:

- `asar/execution/rag/` for corpus download, chunking, embedding, indexing, and retrieval
- `asar/providers/corpus_search.py` as a `SearchClientProtocol` adapter over the local corpus

This preserves:

- existing orchestration
- the `WebSearchExecutor` normalization path
- downstream `EvidenceItem` consumers in memory, deliberation, and verification

See also [ADR-005](architecture/decision-log.md#adr-005-keep-corpus-backed-rag-inside-the-executionsearch-boundary).

## Dataset Selected

Selected dataset: `BeIR/scifact`

Why this dataset:

1. It is directly useful for research-style retrieval and grounding.
2. It is small enough to integrate automatically and repeatedly.
3. Its corpus is already document-like and easy to normalize into chunked text.
4. It is a clean first fit for ASAR’s evidence-first execution model.

### Size Check

The download size was probed from Hugging Face dataset metadata before download.
The mirrored files used by this integration were:

- `corpus.jsonl.gz` — `2,758,600` bytes
- `queries.jsonl.gz` — `49,271` bytes

Total automated download size:

- `2,807,871` bytes

This is well below the 2GB constraint.

### Why Other Options Were Not Selected

- `HotpotQA`: useful, but more multi-hop and annotation-heavy than needed for the first clean integration.
- `Natural Questions`: strong benchmark, but much larger and less convenient for a first under-2GB automatic bootstrap.
- `QASPER` / larger long-document QA corpora: attractive for later, but a worse first fit for a minimal, deterministic integration.

SciFact is not the only reasonable choice, but it is the best first choice for
shipping a real subsystem quickly without taking on dataset-scale complexity.

## Filesystem Layout

The prepared corpus lives under a dedicated dataset root:

```text
data/corpora/<dataset>/
  raw/
  normalized/
  index/
    qdrant/
```

For SciFact the concrete paths are:

- `data/corpora/scifact/raw/`
- `data/corpora/scifact/normalized/`
- `data/corpora/scifact/index/`
- `data/corpora/scifact/index/qdrant/`

The key generated artifacts are:

- `raw/corpus.jsonl.gz`
- `raw/queries.jsonl.gz`
- `normalized/documents.jsonl`
- `normalized/queries.jsonl`
- `normalized/qrels.jsonl`
- `index/chunks.jsonl`
- `index/manifest.json`

## Ingestion Design

The ingestion stack is intentionally modular:

1. `SciFactDatasetAdapter`
   - probes remote size
   - enforces the under-2GB constraint
   - downloads the raw mirrored files
   - normalizes raw rows into internal `CorpusDocument` records

2. `DocumentAwareChunker`
   - preserves sections/headings when available
   - groups paragraphs before enforcing token limits
   - adds overlaps and metadata-rich chunk records

3. `QdrantChunkIndex`
   - stores dense embeddings and metadata in local Qdrant

4. `HybridCorpusRetriever`
   - dense retrieval from Qdrant
   - lexical retrieval via BM25
   - reciprocal-rank fusion for the final ranked chunk list

5. `CorpusSearchClient`
   - adapts retrieval hits back into `SearchResponse`
   - lets `WebSearchExecutor` keep normalizing everything into `EvidenceItem`

## Chunking Strategy

The chunker is document-aware rather than purely fixed-size.

Chunking order:

1. split by heading/section if structure is present
2. split section text into paragraphs
3. group paragraph blocks toward a target token budget
4. split oversized paragraphs by sentence when needed
5. enforce overlap between adjacent chunks

Default policy:

- target chunk size: `450` tokens
- max chunk size: `650` tokens
- overlap: `80` tokens
- minimum chunk size: `120` tokens

Each chunk preserves:

- `dataset_name`
- `doc_id`
- `chunk_id`
- `title`
- `section`
- `source_type`
- `source_path` / `source_url`
- `tags`
- `trust_label`
- token and character counts
- document metadata propagated from the normalized source record

This keeps chunks inspectable and ready for future metadata filters.

## Vector DB Choice

Chosen vector DB: `Qdrant`

Why Qdrant instead of pgvector:

1. simpler local setup for a file-backed first version
2. natural fit for metadata-rich chunk payloads
3. no need to introduce a SQL service dependency yet
4. good upgrade path for later metadata filters and hybrid retrieval extensions

This first version uses local Qdrant storage under the dataset’s `index/qdrant/`
directory instead of requiring a separately managed server.

## Embedding Strategy

Default production backend:

- `FastEmbedTextEmbedder`
- default model: `BAAI/bge-small-en-v1.5`

Additional deterministic fallback:

- `HashingTextEmbedder`

Why the hashing backend exists:

- local smoke tests and CI need a deterministic, zero-network path
- it provides a fully working vector DB pipeline even in constrained environments
- it avoids making the first integration depend entirely on external model downloads

Important status note:

- the production `fastembed` path is implemented and is the default backend
- the fully validated end-to-end bootstrap in this session used the deterministic hashing backend
- this was necessary because the environment-sensitive model bootstrap path did not complete cleanly during validation

## Retrieval Strategy

This first version uses hybrid retrieval:

1. dense semantic retrieval from Qdrant
2. lexical retrieval with `rank-bm25`
3. reciprocal-rank fusion (RRF)

Why not dense-only:

- lexical retrieval is cheap and materially helps exact scientific or technical terms
- hybrid retrieval reduces the risk of missing obvious lexical matches
- RRF is simple, deterministic, and easy to extend later

Current retrieval output:

- top-k chunk hits
- chunk text
- chunk metadata
- fused, dense, and lexical scores/ranks

## Integration With The Current App

The integration points are intentionally small:

- `asar/providers/factory.py`
  - new `ASAR_SEARCH_PROVIDER=corpus` option
- `asar/providers/corpus_search.py`
  - adapts corpus hits to `SearchClientProtocol`
- `asar/execution/web_search_executor.py`
  - already normalizes search hits into `EvidenceItem`
  - now also accepts provider payloads with `source_type=document`

This means the rest of the app still sees:

- `TaskPacket` in
- `EvidenceItem` out

No new orchestration layer, no new public schema, and no bypass around execution.

### Runtime Configuration

Core environment variables:

```bash
export ASAR_SEARCH_PROVIDER=corpus
export ASAR_CORPUS_ROOT=data/corpora
export ASAR_CORPUS_DATASET=scifact
export ASAR_RAG_EMBED_BACKEND=fastembed
export ASAR_RAG_EMBED_MODEL=BAAI/bge-small-en-v1.5
```

Local deterministic fallback:

```bash
export ASAR_RAG_EMBED_BACKEND=hashing
export ASAR_RAG_HASH_DIMENSION=256
```

## Current Limitations

1. Only SciFact is automated in the first version.
2. Dataset normalization is adapter-based but not yet generalized into a multi-dataset registry.
3. The Hugging Face mirrored files used here did not expose qrels in the same automated path, so `qrels.jsonl` is currently written as empty during bootstrap.
4. The default production embedder path depends on a model download that may be slow or environment-sensitive on first run.
5. Retrieval is hybrid dense + BM25 only; there is no reranker yet.
6. Corpus routing is explicit by config; there is no retriever router that blends web and corpus retrieval yet.

## Validation Performed

Validated in code/tests:

- chunking shape and metadata invariants
- hybrid retrieval returns ranked chunks with metadata
- smoke path from chunk/index → corpus search client → `WebSearchExecutor` → `EvidenceItem`
- factory wiring for corpus mode with hashing backend

Validated on real SciFact artifacts:

- dataset size probe
- raw file download
- document normalization
- chunk generation

Validated end-to-end in a deterministic local mode:

- SciFact corpus indexed in Qdrant with the hashing embedder
- retrieval results normalized into the app’s existing evidence flow
- validated local corpus root: `data/corpora_hash/scifact`

## Recommended Next Improvements

1. Add qrels-aware evaluation utilities for SciFact retrieval quality.
2. Add a second corpus adapter after the SciFact path is stable.
3. Add optional document-level caps / source-diversity caps in retrieval.
4. Add a retriever router that can combine local corpus retrieval with web search.
5. Revisit the first-run production embedding bootstrap so the fastembed path is easier to validate automatically.
