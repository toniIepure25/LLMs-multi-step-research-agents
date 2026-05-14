# Experiment: End-to-end RAG + safety vertical slice

## Hypothesis
The ASAR v0 pipeline can be driven by a real RAG retrieval substrate over a
local SciFact corpus and a safety filter — with **zero changes to the
orchestrator core** — by plugging in:

- a new `SearchClientProtocol` implementation (`CorpusSearchClient`)
- a wrapper `SafetyAwareRunner` around the orchestrator

If the architectural seams are correct, evidence flowing into the deliberation
layer should carry full provenance from the retriever (chunk_id, doc_id,
dense_rank, lexical_rank, fused RRF score, trust_label) without modifying
any schema.

## Setup

| Item | Value |
|------|-------|
| Dataset | `BeIR/scifact` (5,183 documents, 4.5 MB parquet) |
| Chunker | `DocumentChunker(target=450, max=650, overlap=80)` |
| Chunks produced | **5,208** |
| Embedder | `HashingEmbedder(dim=384)` (deterministic, no GPU) |
| Vector index | `QdrantVectorIndex` (local on-disk) |
| Lexical index | `BM25Index` (rank_bm25) |
| Fusion | Reciprocal-rank fusion, `k=60` |
| Safety filter | `KeywordSafetyFilter` (regex baseline) |
| Demo goal | "What is known about BRCA1 in breast cancer?" |
| Mode | `mock` LLM + `corpus` search + `safety on` |
| Host | macOS / Apple Silicon (no GPU) |
| Reproducer | `ASAR_SAFETY_ENABLED=1 ASAR_SEARCH_PROVIDER=corpus uv run python -m asar.demo "What is known about BRCA1 in breast cancer?" --output-dir <out>` |

## Stages and timings (RAG CLI)

```
[1/4] Preparing scifact ............ 0.02 s  (cached)
[2/4] Chunking (5183 → 5208) ....... 0.27 s
[3/4] Embedding & indexing ......... 2.93 s
[4/4] Probe retrieval .............. 0.01 s
                                     -------
                                     3.23 s total
```

## Probe retrieval (CLI, hashing embedder)

Query: `"What causes BRCA1-related cancers?"`

| Rank | Doc ID    | Fused score | Snippet |
|------|-----------|-------------|---------|
| 1    | 1866911   | 0.0323      | Basal-like breast cancers arising in women carrying mutations in the BRCA1 gene... |
| 2    | 5372773   | 0.0164      | Human cytomegalovirus (HCMV) expresses several homologues of human interleukin 10 (hIL-10)... |
| 3    | 22975806  | 0.0161      | For individuals genetically predisposed to breast and ovarian cancer through inheritance of a mutant BRCA allele... |
| 4    | 3285322   | 0.0159      | Mutations in the BRCA1 and BRCA2 genes confer greater risk of developing breast cancer... |

Even with the **hashing fallback embedder** (purely deterministic, no model
weights), the top-1 hit is the gold BRCA1 paper. With FastEmbed
(`BAAI/bge-small-en-v1.5`, dim=384) the ranking is expected to improve
materially.

## End-to-end demo (orchestrator)

The full v0 pipeline ran with:

- `SimplePlanner` (deterministic mock)
- `WebSearchExecutor(CorpusSearchClient)` (real SciFact RAG)
- `WorkingMemory`
- `SimpleSynthesizer` (deterministic mock)
- `EvidenceChecker` (groundedness)
- `ExperimentLogger`
- wrapped in `SafetyAwareRunner` (pre-flight + post-flight)

Result:

- 3 plan steps, 3 evidence items, 3 claims, no contradictions
- Every evidence item carries `source_name="corpus:scifact"` and a `raw_payload`
  block with `chunk_id`, `doc_id`, `dense_rank`, `lexical_rank`, `fused_score`,
  `trust_label="peer_reviewed"`, `section`, and `tags`
- `safety.json` shows pre-flight and post-flight reports, both clean
  (`blocked=false`, `max_toxicity=0.0`, `max_injection=0.0`)
- Tests: **182 passed** across the full suite (RAG, safety, local LLM,
  v0 baseline) — zero regressions

## Artifacts

- [output.json](artifacts/output.json) — the full `ResearchOutput` with claims, evidence, and provenance
- [experiment.json](artifacts/experiment.json) — the `ExperimentRecord` artifact
- [safety.json](artifacts/safety.json) — pre- and post-flight safety reports

## Conclusion

The architectural seams hold. The orchestrator was never modified — RAG was
added as a new `SearchClientProtocol` implementation, and safety was added as
a `SafetyAwareRunner` wrapper that introspects the existing
`ResearchOutput` schema. This validates invariants 1 (grounded output),
2 (typed boundaries), 6 (swappable modules), and 7 (orchestration is the only
router).
