# System Overview

> Parent: [PROJECT_DOSSIER.md § System Layers](../../PROJECT_DOSSIER.md#6-system-layers)
> See also: [v0-canonical-architecture.md](v0-canonical-architecture.md) · [component-map.md](component-map.md) · [dataflow.md](dataflow.md) · [decision-log.md](decision-log.md)

## Architectural Layers

ASAR has eight layers. Each has a defined responsibility, typed inputs/outputs, and can be swapped independently as long as the protocol contract in [`asar/core/protocols.py`](../../asar/core/protocols.py) holds.

Current implementation target: the frozen v0 sequential vertical slice defined in [v0-canonical-architecture.md](v0-canonical-architecture.md). This document describes the full architecture and calls out where v0 is intentionally narrower.

```
┌──────────────────────────────────────────────────────┐
│                  ORCHESTRATION                        │
│  Lifecycle management, dispatch, inter-layer routing  │
├──────────┬───────────┬───────────────────────────────┤
│ PLANNING │ EXECUTION │       DELIBERATION            │
│          │           │                               │
│ Goal     │ Search    │ Critique, synthesis,          │
│ decomp,  │ Retrieval │ conflict detection,           │
│ plan     │ Parsing   │ multi-perspective             │
│ struct   │ Tool use  │ reasoning                     │
├──────────┴───────────┴───────────────────────────────┤
│                    MEMORY                             │
│  Working memory, compressed summaries, LTM hooks     │
├──────────────────────────────────────────────────────┤
│                   GROUNDING                           │
│  Evidence normalization, semantic triples,            │
│  source tracking, provenance chains                   │
├──────────────────────────────────────────────────────┤
│                  VERIFICATION                         │
│  Claim checking, citation validation,                 │
│  consistency checks, termination conditions           │
├──────────────────────────────────────────────────────┤
│                  EVALUATION                           │
│  Benchmarks, metrics, experiment logging,             │
│  failure taxonomy                                     │
└──────────────────────────────────────────────────────┘
```

## Layer Contracts

Each layer's contract specifies its input, output, and per-layer invariant. Protocol definitions live in [`asar/core/protocols.py`](../../asar/core/protocols.py). Schema types live in [`schemas/`](../../schemas/).

### planning (`asar/planning/`)
- **Input:** Research goal (`str` + optional constraints)
- **Output:** [`ResearchPlan`](../../schemas/research_plan.py) containing ordered/parallel `PlanStep`s
- **Invariant:** Every `PlanStep` has a typed expected output and success criteria
- **Protocol:** `PlannerProtocol`

### execution (`asar/execution/`)
- **Input:** [`TaskPacket`](../../schemas/task_packet.py)
- **Output:** [`EvidenceItem`](../../schemas/evidence_item.py)(s) with source metadata
- **Invariant:** Executors are stateless — all context comes from the `TaskPacket`
- **Protocol:** `ExecutorProtocol`

### deliberation (`asar/deliberation/`)
- **Input:** `list[EvidenceItem]` + optional `ResearchPlan` context
- **Output:** [`DecisionPacket`](../../schemas/decision_packet.py) with synthesis, conflicts, and confidence
- **Invariant:** Conflicts are preserved, not silently resolved
- **Protocol:** `DeliberationProtocol`

### memory (`asar/memory/`)
- **Input:** Any typed artifact for storage/retrieval
- **Output:** Retrieved artifacts, memory state metadata
- **Invariant:** Memory has explicit tiers — working, compressed, evicted — and the tier is always queryable
- **Protocol:** `MemoryProtocol`

### grounding (`asar/grounding/`)
- **Input:** `list[EvidenceItem]`
- **Output:** Normalized evidence, graph-ready triples, [`CitationRecord`](../../schemas/citation_record.py)(s)
- **Invariant:** Every output triple links back to a source `EvidenceItem`
- **Protocol:** `GroundingProtocol`

### verification (`asar/verification/`)
- **Input:** `DecisionPacket` (from deliberation) + `list[EvidenceItem]` (v0). Phase 2 will also accept `list[CitationRecord]` from grounding.
- **Output:** [`VerificationResult`](../../schemas/verification_result.py) containing per-claim `ClaimVerification` verdicts (`supported`, `unsupported`, `insufficient`, `contradicted`)
- **Invariant:** Verification **never modifies claims** — it produces a separate `VerificationResult`, not a mutated `DecisionPacket`
- **v0 note:** `EvidenceChecker` is weak deterministic support checking, not full truth adjudication
- **Protocol:** `VerificationProtocol`

### evaluation (`asar/evaluation/`)
- **Input:** Run artifacts, config, benchmark definitions
- **Output:** Metrics, scores, failure analysis — stored as [`ExperimentRecord`](../../schemas/experiment_record.py)
- **Invariant:** Evaluation is post-hoc and deterministic given the same inputs
- **Protocol:** `EvaluationProtocol`

### orchestration (`asar/orchestration/`)
- **Input:** Research goal + config
- **Output:** Coordinated execution across all layers
- **Responsibility:** Lifecycle management, error handling, dispatch, inter-layer routing
- **Constraint:** This is the **only** module that imports and routes between layers. Layers never call each other directly.

## Communication Protocol

All inter-layer communication uses typed schemas from [`schemas/`](../../schemas/). The orchestration layer is the sole router — see [dataflow.md](dataflow.md) for the full diagram.

v0 routing (grounding inactive, sequential):
```
orchestration
  ├── calls planning to produce ResearchPlan
  ├── creates TaskPackets, dispatches sequentially to execution
  ├── stores EvidenceItems in memory
  ├── triggers deliberation with accumulated evidence → DecisionPacket
  ├── sends DecisionPacket + evidence to verification → VerificationResult
  ├── logs run to evaluation → ExperimentRecord
  └── assembles ResearchOutput → writes to disk
```

v0 explicitly excludes re-planning, parallel executor dispatch, grounding-driven citations, multi-perspective debate, and advanced memory compression.

Full routing (Phase 2+, grounding active):
```
orchestration
  ├── dispatches TaskPackets to execution
  ├── routes EvidenceItems to grounding → CitationRecords
  ├── feeds grounded evidence to memory
  ├── triggers deliberation with accumulated evidence
  ├── sends DecisionPacket + evidence + CitationRecords to verification
  ├── logs everything to evaluation
  └── manages planning's re-planning cycle
```

## Assumptions

**Single-process architecture** (Phase 0–2). All layers run in a single Python process. Distributed execution is a Phase 4+ concern. This simplifies development but limits parallelism to async/threading.

**Python baseline.** Supported development/runtime target is Python 3.11+. Validation under Python 3.10.x is non-canonical.

## Open Design Questions

- Error propagation protocol: how executor failures surface to orchestration and trigger re-planning. See [OQ-A4](../research/open-questions.md).
- Parallel execution scheduling strategy. See [OQ-A3](../research/open-questions.md).
