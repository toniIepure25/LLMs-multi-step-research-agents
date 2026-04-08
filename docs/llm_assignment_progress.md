# LLM Assignment Progress

This file is intended to be shared asynchronously as a lightweight project
progress document.

## Project

- **Project name:** ASAR — Agentic Structured Autonomous Researcher
- **Team name:** `TBD_TEAM_NAME`
- **Team members:** `TBD_MEMBER_1`, `TBD_MEMBER_2`, `TBD_MEMBER_3`

## Goal

Integrate a real corpus-backed RAG subsystem into the existing ASAR application
without redesigning the whole pipeline, while keeping the implementation
modular, typed, and production-oriented.

## Current Status

- Core application pipeline already exists and remains intact.
- A first real RAG subsystem has been integrated into the execution/search path.
- The first integrated dataset is `BeIR/scifact`.
- Document-aware chunking is implemented.
- Qdrant is integrated as the vector database.
- Hybrid retrieval is implemented: dense retrieval + BM25 + reciprocal-rank fusion.
- Retrieved chunks are normalized into the existing `EvidenceItem` abstraction.

## Key Technical Decisions

### Dataset

- **Chosen dataset:** `BeIR/scifact`
- **Reason:** small, useful, easy to normalize, under the 2GB limit
- **Size checked before download:** yes
- **Observed download size:** about `2.8 MB`

### Chunking

- section-aware when structure exists
- paragraph grouping before token enforcement
- sentence fallback for oversized text
- overlap preserved between adjacent chunks
- metadata-rich chunks

Default configuration:

- target tokens: `450`
- max tokens: `650`
- overlap: `80`
- minimum chunk size: `120`

### Vector Database

- **Chosen DB:** Qdrant
- **Reason:** easy local setup, metadata-friendly, good first production fit

### Embeddings / Models

- **Production embedder:** `BAAI/bge-small-en-v1.5` through FastEmbed
- **Deterministic fallback:** hashing embedder for local smoke tests and constrained environments

### Retrieval Strategy

- dense semantic retrieval
- lexical retrieval with BM25
- reciprocal-rank fusion

## What Works Right Now

- dataset size check
- dataset download
- normalization into internal corpus documents
- chunk generation
- local Qdrant indexing
- retrieval with metadata
- normalization into `EvidenceItem`
- tests passing

## Validation Summary

- targeted RAG tests added
- full test suite passing
- real indexed SciFact corpus validated in a clean local root

## Current Limitations

- only one automated corpus is integrated so far
- qrels are not yet available in the same automated mirrored dataset path
- production FastEmbed bootstrap can be environment-sensitive on the first model fetch
- corpus retrieval exists as an optional backend, not yet the default runtime path

## Recommended Next Step

- add qrels-aware retrieval evaluation for SciFact
- then extend to one additional corpus or a retriever router if needed
