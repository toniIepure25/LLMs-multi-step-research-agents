# v0 Canonical Architecture

> Parent: [PROJECT_DOSSIER.md § Roadmap](../../PROJECT_DOSSIER.md#15-roadmap)
> See also: [system-overview.md](system-overview.md) · [component-map.md](component-map.md) · [dataflow.md](dataflow.md)

This document defines the exact scope of the v0 system — the first end-to-end vertical slice. v0 exercises six protocol layers (planning, execution, memory, deliberation, verification, evaluation) plus the orchestration coordinator in their simplest forms. It is the canonical Phase 1 implementation target.

## Status

- v0 is now frozen
- Frozen historical live baseline: [experiments/notes/v0_tier1_eval_set_004.md](../../experiments/notes/v0_tier1_eval_set_004.md)
- v0 tuning is considered complete for now
- Active experimental successor baseline: [experiments/notes/v1_tier1_eval_set_004.md](../../experiments/notes/v1_tier1_eval_set_004.md)
- The next architectural work should start from the v1-minimal baseline described in [v1-minimal-architecture.md](v1-minimal-architecture.md)

## Frozen Decisions

These decisions are frozen for v0 and should be treated as the single source of truth for Phase 1 foundations:

- Package name is `asar`
- v0 is single-process, sequential, and handles one research goal at a time
- v0 component names are `SimplePlanner`, `WebSearchExecutor`, `WorkingMemory`, `SimpleSynthesizer`, `EvidenceChecker`, `ExperimentLogger`, and `SequentialOrchestrator`
- `VerificationProtocol.verify()` returns `VerificationResult` and does not mutate claims
- `ResearchOutput` is a required v0 artifact
- `grounding` exists conceptually but `CitationRecord`-heavy handling is postponed to Phase 2
- v0 verification is weak deterministic support checking, not full truth adjudication
- v0 has no re-planning loop, no parallel execution, no multi-perspective debate, and no advanced memory compression
- Supported development/runtime baseline is Python 3.11+; validation under Python 3.10.x is non-canonical

---

## 1. v0 Goal

Answer a single factual research question end-to-end, producing a typed `ResearchOutput` artifact that contains a plan, collected evidence with provenance, synthesized claims linked to evidence, per-claim verification verdicts, and experiment metadata.

---

## 2. v0 Scope

v0 is a single-process, sequential, text-only pipeline. Six protocol layers are active, `orchestration` is active as the coordinator, `grounding` remains inactive until Phase 2, and two support modules are active.

**v0 does:**
- Decompose a research goal into sequential plan steps (`planning`)
- Execute each step via web search (`execution`)
- Store evidence in working memory (`memory`)
- Synthesize evidence into claims with evidence links (`deliberation` — single-pass)
- Check claims against evidence with deterministic logic (`verification` — no LLM)
- Log the run as an `ExperimentRecord` and compute metrics (`evaluation`)
- Produce a typed `ResearchOutput` artifact written to disk

**v0 does NOT:**
- Normalize evidence into `CitationRecord`s (Phase 2 — `grounding`)
- Build a knowledge graph (Phase 2 — `grounding`)
- Execute tasks in parallel (Phase 3 — `orchestration`)
- Re-plan based on execution feedback (Phase 2 — `orchestration`)
- Compress or tier memory (Phase 2 — `memory`)
- Use embedding-based retrieval (Phase 2 — `memory`)
- Run multi-perspective deliberation / debate (Phase 3 — `deliberation`)
- Use LLM-based verification (Phase 2 — `verification`)
- Run full benchmark suites or ablations (Phase 4 — `evaluation`)

---

## 3. v0 Non-Goals

These are out of scope for v0 and must not be worked on:

- Any UI or chat interface
- Parallel or distributed execution
- Multiple search APIs or executor types
- Re-planning loops
- Memory compression, eviction, or embedding retrieval
- CitationRecord generation or knowledge graphs
- Multi-perspective deliberation (advocate/critic/red-team)
- LLM-based verification or human-in-the-loop verification
- Ablation framework or experiment dashboards

---

## 4. Exact Component List

### Active Protocol Layers (6)

| Layer | Module | Protocol | v0 Implementation |
|-------|--------|----------|--------------------|
| `planning` | `asar/planning/` | `PlannerProtocol` | `SimplePlanner` — one LLM call, goal → `ResearchPlan` with sequential `PlanStep`s. `replan()` raises `NotImplementedError`. |
| `execution` | `asar/execution/` | `ExecutorProtocol` | `WebSearchExecutor` — one search API call per `TaskPacket` → `list[EvidenceItem]` with `SourceMetadata`. |
| `memory` | `asar/memory/` | `MemoryProtocol` | `WorkingMemory` — Python dict keyed by `evidence_id`. `compress()` is a no-op returning 0. |
| `deliberation` | `asar/deliberation/` | `DeliberationProtocol` | `SimpleSynthesizer` — one LLM call over all evidence → `DecisionPacket` with `Claim`s referencing `evidence_id`s. No debate, no multi-perspective. |
| `verification` | `asar/verification/` | `VerificationProtocol` | `EvidenceChecker` — deterministic Python, no LLM. Weak support checking only: referential integrity + basic keyword relevance → `VerificationResult`. |
| `evaluation` | `asar/evaluation/` | `EvaluationProtocol` | `ExperimentLogger` — builds `ExperimentRecord`, computes metrics, writes to disk. |

### Inactive Layer (1)

| Layer | Module | Protocol | When |
|-------|--------|----------|------|
| `grounding` | `asar/grounding/` | `GroundingProtocol` | Phase 2. Requires evidence normalization design ([OQ-A2](../research/open-questions.md)). |

### Coordinator

| Module | v0 Implementation |
|--------|-------------------|
| `orchestration` (`asar/orchestration/`) | `SequentialOrchestrator` — drives the full pipeline sequentially: plan → execute → store → synthesize → verify → evaluate → write `ResearchOutput`. |

### Support Modules (2)

| Module | Path | v0 Responsibility |
|--------|------|--------------------|
| `core` | `asar/core/` | Protocol definitions (`protocols.py`), base exceptions |
| `common` | `asar/common/` | TOML config loading, logging setup, ID generation |

---

## 5. Exact Schemas Used in v0

### Active — exercised in the v0 pipeline

| Schema | File | Produced by | Consumed by |
|--------|------|------------|-------------|
| `ResearchPlan` | `schemas/research_plan.py` | `planning` | `orchestration` |
| `PlanStep` | `schemas/research_plan.py` | `planning` | `orchestration` |
| `TaskPacket` | `schemas/task_packet.py` | `orchestration` | `execution` |
| `EvidenceItem` | `schemas/evidence_item.py` | `execution` | `memory`, `deliberation`, `verification` |
| `SourceMetadata` | `schemas/evidence_item.py` | `execution` | (output provenance) |
| `DecisionPacket` | `schemas/decision_packet.py` | `deliberation` | `verification` |
| `Claim` | `schemas/decision_packet.py` | `deliberation` | `verification` |
| `VerificationResult` | `schemas/verification_result.py` | `verification` | `orchestration` (output) |
| `ClaimVerification` | `schemas/verification_result.py` | `verification` | (inside `VerificationResult`) |
| `ResearchOutput` | `schemas/research_output.py` | `orchestration` | (disk artifact) |
| `ExperimentRecord` | `schemas/experiment_record.py` | `evaluation` | (disk artifact) |

### Exists but not exercised until Phase 2

| Schema | File | Why deferred |
|--------|------|-------------|
| `CitationRecord` | `schemas/citation_record.py` | Requires `grounding` layer. v0 verification checks evidence directly. |

---

## 6. Exact Protocol Contracts for v0

All protocols are defined in `asar/core/protocols.py`. These are the exact signatures that v0 implementations must satisfy.

```python
class PlannerProtocol(Protocol):
    async def plan(self, goal: str, constraints: dict | None = None) -> ResearchPlan: ...
    async def replan(self, plan_id: str, feedback: str) -> ResearchPlan: ...

class ExecutorProtocol(Protocol):
    async def execute(self, task: TaskPacket) -> list[EvidenceItem]: ...

class MemoryProtocol(Protocol):
    async def store(self, item: EvidenceItem) -> str: ...
    async def retrieve(self, query: str, limit: int = 10) -> list[EvidenceItem]: ...
    async def compress(self) -> int: ...

class DeliberationProtocol(Protocol):
    async def deliberate(self, evidence: list[EvidenceItem], context: str | None = None) -> DecisionPacket: ...

class VerificationProtocol(Protocol):
    async def verify(self, decision: DecisionPacket, evidence: list[EvidenceItem]) -> VerificationResult: ...

class EvaluationProtocol(Protocol):
    async def evaluate(self, run_artifacts: dict) -> dict: ...
    async def log_experiment(self, record: ExperimentRecord) -> None: ...
```

Key decisions reflected here:
- `VerificationProtocol.verify()` takes `list[EvidenceItem]`, not `list[CitationRecord]`. CitationRecords require the grounding layer (Phase 2). In Phase 2, the signature will evolve to accept both.
- `VerificationProtocol.verify()` returns `VerificationResult`, not `DecisionPacket`. Verification never mutates claims.
- v0 verification is weak deterministic support checking. It is not a full truth adjudication system.
- `GroundingProtocol` is defined but not exercised in v0.

---

## 7. Exact Output Artifact Shape

A complete v0 run produces a single `ResearchOutput` object, serialized as JSON to `experiments/runs/<timestamp>_<slug>/output.json`.

```python
ResearchOutput(
    goal="What were the main causes of the 2008 financial crisis?",
    plan=ResearchPlan(
        plan_id="...",
        goal="...",
        steps=[PlanStep(...), PlanStep(...), ...],
    ),
    evidence=[
        EvidenceItem(evidence_id="...", content="...", source=SourceMetadata(...)),
        ...
    ],
    decision=DecisionPacket(
        decision_id="...",
        plan_id="...",
        claims=[
            Claim(claim_id="...", text="...", supporting_evidence_ids=["..."], ...),
            ...
        ],
        conflicts=[...],
    ),
    verification=VerificationResult(
        decision_id="...",
        claim_verdicts=[
            ClaimVerification(claim_id="...", verdict="supported", ...),
            ...
        ],
        summary="4/5 claims supported, 1 insufficient",
    ),
    experiment=ExperimentRecord(
        experiment_id="...",
        name="...",
        hypothesis="...",
        metrics={"groundedness": 0.80, "evidence_utilization": 0.65, "plan_coverage": 1.0},
    ),
)
```

---

## 8. v0 Data Flow

```
Research Goal (str)
  │
  ▼
┌────────────────┐
│    planning     │  goal → ResearchPlan
└───────┬────────┘
        │ ResearchPlan
        ▼
┌────────────────┐
│  orchestration  │  for each PlanStep: create TaskPacket
└───┬────────────┘
    │ TaskPacket (sequential, one at a time)
    ▼
┌────────────────┐
│   execution     │  TaskPacket → list[EvidenceItem] (web search)
└───────┬────────┘
        │ list[EvidenceItem]
        ▼
┌────────────────┐
│    memory       │  store each EvidenceItem
└───────┬────────┘
        │ (all evidence accumulated)
        ▼
┌────────────────┐
│  deliberation   │  list[EvidenceItem] → DecisionPacket with Claims
└───────┬────────┘
        │ DecisionPacket
        ▼
┌────────────────┐
│  verification   │  DecisionPacket + list[EvidenceItem] → VerificationResult
└───────┬────────┘
        │ VerificationResult
        ▼
┌────────────────┐
│   evaluation    │  all artifacts → ExperimentRecord with metrics
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  orchestration  │  assemble ResearchOutput → write to disk
└────────────────┘
```

---

## 9. Success Criteria

v0 is complete when all of the following hold:

1. **End-to-end execution.** Given a Tier 1 question, the system produces a `ResearchOutput` with all fields populated.

2. **Evidence has provenance.** Every `EvidenceItem` in the output has a `SourceMetadata` with at least `source_type`, `url`, and `raw_snippet` populated.

3. **Claims link to evidence.** Every `Claim` in the `DecisionPacket` has at least one entry in `supporting_evidence_ids` that references an `EvidenceItem` in the output.

4. **Verification is independent.** The `VerificationResult` is produced by `EvidenceChecker` (deterministic, no LLM), not by the same module that produced the claims.

5. **Verification is modest by design.** v0 checks for basic evidence support, not full truth adjudication.

6. **Typed throughout.** Every inter-layer boundary uses schemas from `schemas/`. No raw string or dict passing between layers.

7. **Config-driven.** Model provider, model ID, and pipeline toggles are read from `config/*.toml`.

8. **Tested.** Each component has unit tests. The full pipeline has an integration test (may use mocked LLM/search responses).

9. **Logged.** The run is recorded as an `ExperimentRecord` with git commit, config snapshot, seed, and timing.

10. **Metrics computed.** At least three metrics:
   - `groundedness` — fraction of claims with verdict `SUPPORTED`
   - `evidence_utilization` — fraction of `EvidenceItem`s referenced by at least one claim
   - `plan_coverage` — fraction of `PlanStep`s that produced at least one `EvidenceItem`

---

## 10. What is Postponed and Why

| Feature | Phase | Why |
|---------|-------|-----|
| `grounding` layer / `CitationRecord` generation | Phase 2 | Requires evidence normalization design ([OQ-A2](../research/open-questions.md)). v0 verification checks evidence directly — provenance is tracked via `SourceMetadata`. |
| Re-planning loop | Phase 2 | Requires error propagation design ([OQ-A4](../research/open-questions.md)). v0 is single-pass. |
| Parallel execution | Phase 3 | Requires scheduling strategy ([OQ-A3](../research/open-questions.md)). v0 dispatches sequentially. |
| Memory compression / eviction | Phase 2 | v0 evidence set is small (15–25 items). Compression decisions ([OQ-M1](../research/open-questions.md)) not yet needed. |
| Embedding-based retrieval | Phase 2 | Keyword match is sufficient for small evidence sets. Retrieval strategy ([OQ-M3](../research/open-questions.md)) deferred. |
| Multi-perspective deliberation | Phase 3 | Single-pass synthesis is sufficient to test the typed pipeline. Debate patterns are a research concern. |
| LLM-based verification | Phase 2 | Deterministic checks come first. LLM-based "does this evidence support this claim?" is an enhancement. |
| Full benchmark suite | Phase 4 | 5 questions is enough for a baseline. Expand when the pipeline is stable. |
| Ablation framework | Phase 4 | Requires components to ablate. |

---

## 11. v0 Build Order

Each step produces a testable artifact. Each step is one commit.

| # | What | Module | Test | Depends on |
|---|------|--------|------|-----------|
| 1 | Config loader: read `config/*.toml`, return typed settings | `common` | Unit test: load each config | — |
| 2 | ID generation + logging setup | `common` | Unit test: IDs unique, logs emit | — |
| 3 | `WorkingMemory`: dict store/retrieve, compress no-op | `memory` | Unit test: store, retrieve, compress | schemas |
| 4 | `SimplePlanner`: LLM call → `ResearchPlan` | `planning` | Unit test with mocked LLM | `common` |
| 5 | `WebSearchExecutor`: search API → `list[EvidenceItem]` | `execution` | Unit test with mocked API | `common` |
| 6 | `SimpleSynthesizer`: LLM call → `DecisionPacket` | `deliberation` | Unit test with mocked LLM | schemas |
| 7 | `EvidenceChecker`: deterministic verification | `verification` | Unit test: known inputs → expected verdicts | schemas |
| 8 | `ExperimentLogger`: build record, compute metrics, write | `evaluation` | Unit test: artifacts → valid record | schemas |
| 9 | `SequentialOrchestrator`: wire all layers → `ResearchOutput` | `orchestration` | Integration test with mocks | steps 3–8 |
| 10 | Live run on one Tier 1 question | — | Manual inspection of `output.json` | step 9 |
| 11 | 5 Tier 1 benchmark questions with rubrics | `evaluation` | — | — |
| 12 | Baseline metrics: run pipeline on benchmarks | `evaluation` | — | steps 9–11 |

Steps 1–2 are independent. Steps 3–8 depend only on `common` + schemas and are independent of each other. Step 9 wires everything. Step 10 is the proof.

---

## 12. Relationship to Full Architecture

v0 is a strict subset of the 8-layer architecture in [system-overview.md](system-overview.md). v0 decisions do not constrain later phases:

- `SequentialOrchestrator` will be replaced by a full orchestrator with parallel dispatch and re-planning. Protocol contracts remain the same.
- `WorkingMemory` will gain compression and eviction. `MemoryProtocol.compress()` already exists — v0 implements it as a no-op.
- `SimplePlanner` will be replaced by planners supporting conditional and parallel steps. `PlannerProtocol.replan()` already exists — v0 raises `NotImplementedError`.
- `SimpleSynthesizer` will be replaced by multi-perspective deliberation. `DeliberationProtocol.deliberate()` signature is unchanged.
- `EvidenceChecker` will be enhanced with LLM-based checks and `CitationRecord` support. `VerificationProtocol.verify()` will evolve to also accept `list[CitationRecord]`.
- `ResearchOutput` will grow to include `CitationRecord`s and grounding artifacts when the grounding layer is active.
