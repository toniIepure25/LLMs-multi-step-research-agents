# Next Steps

> See also: [v0-canonical-architecture.md](../docs/architecture/v0-canonical-architecture.md) for exact v0 scope and success criteria.
> Runtime baseline: Python 3.11+ only. Validation observed under Python 3.10.12 was non-canonical and does not change the repository requirement.
> v0 naming is frozen. Do not rename the canonical v0 components while implementing Phase 1 foundations.

## v0 Build Order (Phase 1)

Each step produces a testable artifact. Each step should be one commit. Do them in order — later steps depend on earlier ones.

| # | What | Layer | Depends on | Status |
|---|------|-------|-----------|--------|
| 1 | Config loader: read `config/*.toml`, return typed settings | `common` | — | completed |
| 2 | ID generation + logging setup | `common` | — | completed |
| 3 | `WorkingMemory`: dict store/retrieve, `compress()` no-op | `memory` | schemas | completed |
| 4 | `SimplePlanner`: single LLM call → `ResearchPlan` | `planning` | `common`, schemas | completed |
| 5 | `WebSearchExecutor`: search API → `list[EvidenceItem]` | `execution` | `common`, schemas | completed |
| 6 | `SimpleSynthesizer`: single LLM call over all evidence → `DecisionPacket` with `Claim`s | `deliberation` | schemas | completed |
| 7 | `EvidenceChecker`: deterministic verification, no LLM → `VerificationResult` | `verification` | schemas | completed |
| 8 | `ExperimentLogger`: build `ExperimentRecord`, compute metrics, write to disk | `evaluation` | schemas | completed |
| 9 | `SequentialOrchestrator`: wire all layers → `ResearchOutput` | `orchestration` | steps 3–8 | completed |
| 10 | Integration test: end-to-end on one Tier 1 question (mocked LLM/search) | tests | step 9 | completed |
| 11 | Live run on one Tier 1 question | — | step 10 | not started |
| 12 | 5 Tier 1 benchmark questions with ground-truth rubrics | `evaluation` | — | not started |
| 13 | Baseline metrics: run pipeline on benchmarks, record results | `evaluation` | steps 11–12 | not started |

Steps 1–2 are independent. Steps 3–8 depend only on `common` + schemas and are independent of each other. Step 9 wires everything. Step 10 is the proof.

## Open Decisions Before Starting

- **OQ-P1**: Which search API? Tavily, Brave Search, or SerpAPI. Pick one, add as dependency.
- **OQ-P2**: API key management — env vars for now, revisit later.
- **OQ-A4**: Error handling in executors — decide before step 5. Recommendation: return empty `list[EvidenceItem]` on failure + log, don't raise.

## NOT in v0 (Do Not Implement Yet)

- Re-planning loop (`planning.replan()` raises `NotImplementedError`)
- Parallel execution
- `CitationRecord` generation / knowledge graph (`grounding` layer)
- LLM-based verification (v0 verification is deterministic Python only)
- Multi-perspective deliberation / debate (v0 is single-pass synthesis)
- Memory compression / eviction (`compress()` is a no-op)
- Embedding-based retrieval
- Full benchmark suite or ablation framework

See [v0-canonical-architecture.md § What is Postponed](../docs/architecture/v0-canonical-architecture.md#10-what-is-postponed-and-why) for rationale.
