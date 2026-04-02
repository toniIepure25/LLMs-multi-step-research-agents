# Next Steps

> See also: [v0-canonical-architecture.md](../docs/architecture/v0-canonical-architecture.md) for exact v0 scope and success criteria.
> Runtime baseline: Python 3.11+ only. Validation observed under Python 3.10.12 was non-canonical and does not change the repository requirement.
> v0 naming is frozen. Do not rename the canonical v0 components while implementing Phase 1 foundations.
> Frozen historical v0 baseline: [experiments/notes/v0_tier1_eval_set_004.md](../experiments/notes/v0_tier1_eval_set_004.md)
> Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
> Exploratory v1.1 branch outcome: [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md)
> Exploratory v1.2 branch outcome: [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md)
> Exploratory v1.3 branch outcome: [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](handoff/2026-03-26_v1_3_exploratory_freeze.md)
> Exploratory v1.4 branch outcome: [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](handoff/2026-03-31_v1_4_exploratory_freeze.md)

## Current State

- v0 is frozen for now
- `v0_tier1_eval_set_004` is the frozen historical live baseline
- `v1_tier1_eval_set_004` is the active experimental live baseline for v1-minimal
- v1.1 grounded selection remains exploratory only and was not promoted
- v1.2 mechanism bundling remains exploratory only and was not promoted
- v1.3 mechanism sketching remains exploratory only and was not promoted
- v1.4 slot-grounded drafting remains exploratory only and was not promoted
- v0 tuning is complete
- v1-minimal tuning is paused at the current baseline and should not continue by default
- v1.1 tuning should also stop by default because the focused live 2008 probes did not clear the promotion bar
- v1.2 tuning should also stop by default because the focused live probes did not show clear overall superiority over the active v1-minimal baseline
- v1.3 tuning should also stop by default because the focused live 2008 probe did not show clear superiority to the active v1-minimal baseline
- v1.4 tuning should also stop by default because the focused live 2008 probe did not clear the promotion bar against the active v1-minimal baseline
- Future work should build intentionally from the v1-minimal baseline and begin with a new consciously scoped design step rather than reopening narrow v1.1, v1.2, v1.3, or v1.4 probe loops first
- Transition summary and freeze handoffs:
  - [docs/architecture/v1-minimal-architecture.md](../docs/architecture/v1-minimal-architecture.md)
  - [tasks/handoff/2026-03-20_v1_minimal_baseline_freeze.md](handoff/2026-03-20_v1_minimal_baseline_freeze.md)
  - [docs/architecture/v1_1-grounded-selection-architecture.md](../docs/architecture/v1_1-grounded-selection-architecture.md)
  - [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md)
  - [docs/architecture/v1_2-mechanism-bundling-architecture.md](../docs/architecture/v1_2-mechanism-bundling-architecture.md)
  - [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md)
  - [docs/architecture/v1_3-mechanism-sketching-architecture.md](../docs/architecture/v1_3-mechanism-sketching-architecture.md)
  - [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](handoff/2026-03-26_v1_3_exploratory_freeze.md)
  - [docs/architecture/v1_4-slot-grounded-drafting-architecture.md](../docs/architecture/v1_4-slot-grounded-drafting-architecture.md)
  - [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](handoff/2026-03-31_v1_4_exploratory_freeze.md)

## Baseline Policy

- Frozen historical baseline:
  - [experiments/notes/v0_tier1_eval_set_004.md](../experiments/notes/v0_tier1_eval_set_004.md)
- Active experimental baseline:
  - [experiments/notes/v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md)
- Exploratory only, not promoted:
  - [docs/architecture/v1_1-grounded-selection-architecture.md](../docs/architecture/v1_1-grounded-selection-architecture.md)
  - [experiments/notes/v1_1_2008_probe_001.md](../experiments/notes/v1_1_2008_probe_001.md)
  - [experiments/notes/v1_1_2008_probe_002.md](../experiments/notes/v1_1_2008_probe_002.md)
  - [docs/architecture/v1_2-mechanism-bundling-architecture.md](../docs/architecture/v1_2-mechanism-bundling-architecture.md)
  - [experiments/notes/v1_2_2008_probe_002.md](../experiments/notes/v1_2_2008_probe_002.md)
  - [experiments/notes/v1_2_great_depression_probe_001.md](../experiments/notes/v1_2_great_depression_probe_001.md)
  - [experiments/notes/v1_2_dotcom_probe_001.md](../experiments/notes/v1_2_dotcom_probe_001.md)
  - [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md)
  - [docs/architecture/v1_3-mechanism-sketching-architecture.md](../docs/architecture/v1_3-mechanism-sketching-architecture.md)
  - [experiments/notes/v1_3_2008_probe_001.md](../experiments/notes/v1_3_2008_probe_001.md)
  - [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](handoff/2026-03-26_v1_3_exploratory_freeze.md)
  - [docs/architecture/v1_4-slot-grounded-drafting-architecture.md](../docs/architecture/v1_4-slot-grounded-drafting-architecture.md)
  - [experiments/notes/v1_4_2008_probe_001.md](../experiments/notes/v1_4_2008_probe_001.md)
  - [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](handoff/2026-03-31_v1_4_exploratory_freeze.md)

Use `v0_tier1_eval_set_004` as the historical frozen comparison point.
Use `v1_tier1_eval_set_004` as the current starting point for future work.
Do not use v1.1, v1.2, v1.3, or v1.4 as the default runtime comparison point or baseline.

## What v1-Minimal Added

- explicit candidate claim generation boundary in `deliberation`
- deterministic `ClaimSelector` after generation
- support-aware and question-aware final selection
- better direct-causal claim quality than frozen v0 on the most important live questions

## What To Avoid By Default

- no more narrow v0 tuning
- no more narrow v1-minimal tuning unless a future phase explicitly reopens it
- no default return to probe loops before first documenting a new phase goal

## Recommended Start Point For The Next Phase

- preserve `v0_tier1_eval_set_004` as the historical baseline
- preserve `v1_tier1_eval_set_004` as the active experimental baseline
- treat v1.1, v1.2, v1.3, and v1.4 as exploratory evidence, not as the default runtime path forward
- use [2026-03-20_v1_minimal_baseline_freeze.md](handoff/2026-03-20_v1_minimal_baseline_freeze.md), [2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md), [2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md), [2026-03-26_v1_3_exploratory_freeze.md](handoff/2026-03-26_v1_3_exploratory_freeze.md), and [2026-03-31_v1_4_exploratory_freeze.md](handoff/2026-03-31_v1_4_exploratory_freeze.md) to scope the next phase
- start the next phase with a new consciously scoped design step rather than more narrow tuning of v1-minimal, v1.1, v1.2, v1.3, or v1.4
- only reopen v1.1, v1.2, v1.3, or v1.4 if a new design decision explicitly chooses to revive or replace those approaches

## Archived v0 Build Order (Phase 1)

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
| 11 | Live run on one Tier 1 question | — | step 10 | completed |
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

## Explicitly Not In The First v1 Step

- Grounding or `CitationRecord` handling
- Re-planning
- Parallel execution
- Multi-perspective debate
- Advanced memory
- Benchmark expansion
- Broad verification redesign

## Archived v1-Minimal Transition

The design and implementation sequence for the minimal v1 transition is preserved in [tasks/v1_minimal_plan.md](v1_minimal_plan.md). It is no longer the default active work queue now that [v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md) serves as the active experimental baseline.

## Next Design Step

The next intentional step should be:

- diversity-constrained mechanism slate selection before final claim wording and selection

Reference material:

- [docs/architecture/v1_5-mechanism-slate-selection-architecture.md](../docs/architecture/v1_5-mechanism-slate-selection-architecture.md)
- [tasks/v1_5_mechanism_slate_selection_plan.md](v1_5_mechanism_slate_selection_plan.md)
- [docs/architecture/v1_1-grounded-selection-architecture.md](../docs/architecture/v1_1-grounded-selection-architecture.md)
- [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](handoff/2026-03-21_v1_1_exploratory_freeze.md)
- [docs/architecture/v1_2-mechanism-bundling-architecture.md](../docs/architecture/v1_2-mechanism-bundling-architecture.md)
- [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](handoff/2026-03-25_v1_2_exploratory_freeze.md)
- [docs/architecture/v1_3-mechanism-sketching-architecture.md](../docs/architecture/v1_3-mechanism-sketching-architecture.md)
- [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](handoff/2026-03-26_v1_3_exploratory_freeze.md)
- [docs/architecture/v1_4-slot-grounded-drafting-architecture.md](../docs/architecture/v1_4-slot-grounded-drafting-architecture.md)
- [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](handoff/2026-03-31_v1_4_exploratory_freeze.md)

Why this is the next step:

- v1.1 showed that support-aware selection can help, but was too brittle downstream
- v1.2 showed that earlier structure can help, but deterministic bundles alone were not clearly superior overall
- v1.3 showed that sketch-first structure can preserve mechanism separation, but final mechanism choice still drifted
- v1.4 showed that slot-grounded drafting can be viable, but same-family duplication in the final set remained unresolved
- the next bottleneck is now explicit set composition:
  - preserve three distinct supported mechanisms when available
  - avoid same-family duplication
  - keep target-event fidelity before final wording

The active runtime comparison point remains [v1_tier1_eval_set_004.md](../experiments/notes/v1_tier1_eval_set_004.md). The exploratory branches remain design evidence, not the default runtime path.
