# Open Questions

> See also: [research-agenda.md](research-agenda.md) · [hypotheses.md](hypotheses.md) · [decision-log.md](../architecture/decision-log.md)

Questions that need answers before or during implementation. Tagged with phase and related layer.

## Architecture

- **OQ-A1** [Phase 2] `planning` → `orchestration`: After v0, should the planner return a full plan upfront or stream tasks incrementally?
- **OQ-A2** [Phase 2] `grounding`: Should the knowledge graph be in-memory or backed by a graph database? What scale do we need?
- **OQ-A3** [Phase 3] `execution` → `orchestration`: How should parallel executors coordinate? Shared memory? Message passing? Event bus?
- **OQ-A4** [Phase 1] `execution` → `orchestration`: How should errors propagate? Exceptions? Result types? Error channels?

## Memory

- **OQ-M1** [Phase 2] `memory`: When compression activates after v0, what compression ratio is acceptable for working memory summaries?
- **OQ-M2** [Phase 2] `memory`: When should information be evicted from working memory to long-term storage?
- **OQ-M3** [Phase 3] `memory`: How should retrieval work? Embedding-based? Keyword? Hybrid?

## Verification

- **OQ-V1** [Phase 2] `verification`: What constitutes "sufficient evidence" for a claim? How many independent sources?
- **OQ-V2** [Phase 2] `verification` → `deliberation`: How should conflicting evidence be handled? Majority vote? Confidence weighting?
- **OQ-V3** [Phase 2] `verification`: When should the system give up verifying and mark a claim unverifiable?

## Evaluation

- **OQ-E1** [Phase 1] `evaluation`: What benchmark tasks to start with? Existing datasets or custom? See [benchmarks.md](../evaluation/benchmarks.md).
- **OQ-E2** [Phase 4] `evaluation`: How to evaluate intermediate steps (plan quality, memory quality) vs. end-to-end?
- **OQ-E3** [Phase 4] `evaluation`: Right balance between automated metrics and human evaluation?

## Practical

- **OQ-P1** [Phase 1] `common`: Initial live v0 provider choice is OpenAI for LLM + Brave Search for web search. Fallback strategy remains open for later phases.
- **OQ-P2** [Phase 1] `common`: How should API keys be managed? Environment variables? Secrets manager?
- **OQ-P3** [Phase 2] `execution`: Rate limiting / cost management for tool calls?
