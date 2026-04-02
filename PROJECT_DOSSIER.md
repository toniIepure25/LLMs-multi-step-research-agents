# Project Dossier — ASAR

This is the single source of truth for project context. All other docs reference this file — they do not duplicate it.

For how to *work* in this repo, see [AGENTS.md](AGENTS.md).
For a quick orientation, see [README.md](README.md).

Current architecture status:
- Frozen historical v0 baseline: [experiments/notes/v0_tier1_eval_set_004.md](experiments/notes/v0_tier1_eval_set_004.md)
- Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](experiments/notes/v1_tier1_eval_set_004.md)
- Exploratory v1.1 branch: grounded selection / support attribution, not promoted after focused live probing: [experiments/notes/v1_1_2008_probe_001.md](experiments/notes/v1_1_2008_probe_001.md), [experiments/notes/v1_1_2008_probe_002.md](experiments/notes/v1_1_2008_probe_002.md)
- Exploratory v1.2 branch: deterministic mechanism bundling, not promoted after focused live probing: [experiments/notes/v1_2_2008_probe_002.md](experiments/notes/v1_2_2008_probe_002.md), [experiments/notes/v1_2_great_depression_probe_001.md](experiments/notes/v1_2_great_depression_probe_001.md), [experiments/notes/v1_2_dotcom_probe_001.md](experiments/notes/v1_2_dotcom_probe_001.md)
- Exploratory v1.3 branch: evidence-grounded mechanism sketching, not promoted after the focused live 2008 probe: [experiments/notes/v1_3_2008_probe_001.md](experiments/notes/v1_3_2008_probe_001.md)
- Exploratory v1.4 branch: slot-grounded mechanism drafting, not promoted after the focused live 2008 probe: [experiments/notes/v1_4_2008_probe_001.md](experiments/notes/v1_4_2008_probe_001.md)
- Future work should begin with a new consciously scoped architecture-design step; v1.1 through v1.4 are now design evidence, not the default implementation queue

The frozen v0 sequential vertical slice is defined in [docs/architecture/v0-canonical-architecture.md](docs/architecture/v0-canonical-architecture.md). The implemented v1-minimal transition is summarized in [docs/architecture/v1-minimal-architecture.md](docs/architecture/v1-minimal-architecture.md). The exploratory v1.1 outcome and freeze status are summarized in [docs/architecture/v1_1-grounded-selection-architecture.md](docs/architecture/v1_1-grounded-selection-architecture.md) and [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md). The exploratory v1.2 outcome and freeze status are summarized in [docs/architecture/v1_2-mechanism-bundling-architecture.md](docs/architecture/v1_2-mechanism-bundling-architecture.md) and [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md). The exploratory v1.3 outcome and freeze status are summarized in [docs/architecture/v1_3-mechanism-sketching-architecture.md](docs/architecture/v1_3-mechanism-sketching-architecture.md) and [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md). The exploratory v1.4 outcome and freeze status are summarized in [docs/architecture/v1_4-slot-grounded-drafting-architecture.md](docs/architecture/v1_4-slot-grounded-drafting-architecture.md) and [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md).

---

## Table of Contents

1. [Mission](#1-mission)
2. [Problem Statement](#2-problem-statement)
3. [Why Existing Research Agents Are Not Enough](#3-why-existing-research-agents-are-not-enough)
4. [Proposed Architectural Direction](#4-proposed-architectural-direction)
5. [Core Design Principles](#5-core-design-principles)
6. [System Layers](#6-system-layers)
7. [Key Entities and Data Structures](#7-key-entities-and-data-structures)
8. [Research Hypotheses](#8-research-hypotheses)
9. [Non-Goals](#9-non-goals)
10. [Invariants](#10-invariants)
11. [Open Questions](#11-open-questions)
12. [Experimental Methodology](#12-experimental-methodology)
13. [Evaluation Strategy](#13-evaluation-strategy)
14. [Failure Modes to Track](#14-failure-modes-to-track)
15. [Roadmap](#15-roadmap)
16. [Agent Instructions for Future Modifications](#16-agent-instructions-for-future-modifications)
17. [Glossary](#17-glossary)

---

## 1. Mission

Build a research-grade multi-step autonomous research agent that:
1. Decomposes complex research questions into structured plans
2. Executes plans via typed communication, with parallel workers added in later phases
3. Maintains hierarchical memory across long research sessions
4. Grounds claims in verifiable evidence with provenance tracking
5. Verifies outputs through deterministic constraint checking
6. Supports reproducible experiments and benchmark-driven evaluation

The project name is **ASAR** — Agentic Structured Autonomous Researcher.

---

## 2. Problem Statement

A user poses a complex research question — for example, *"What are the comparative tradeoffs of battery chemistries for grid-scale energy storage?"* A good answer requires:
- decomposing the question into sub-questions (cost, energy density, cycle life, supply chain, environmental impact...)
- searching multiple sources for each sub-question
- evaluating source credibility and resolving conflicting claims
- synthesizing a coherent, cited, balanced answer
- knowing when the answer is complete enough to stop

No single LLM call can do this reliably. The context window is too small. The reasoning is too shallow. The citations are too often fabricated. There is no mechanism for self-correction beyond retry.

ASAR is an attempt to build a system where each of these sub-problems is handled by a dedicated, testable, swappable component — and where the whole pipeline is inspectable, reproducible, and empirically improvable.

---

## 3. Why Existing Research Agents Are Not Enough

| Weakness | Description | How ASAR addresses it |
|----------|------------|----------------------|
| **No planning discipline** | Most agents execute linearly — one query, one response, repeat. There is no explicit plan, no dependency graph, no ability to parallelize. | Dedicated `planning` layer produces a typed `ResearchPlan` with ordered/parallel `PlanStep`s before any execution begins. |
| **Context window as sole memory** | When the conversation exceeds the window, information is silently lost. There is no compression, no tiering, no retrieval. | Dedicated `memory` layer with explicit tiers (working → compressed → evicted) and retrieval interface. |
| **No evidence grounding** | Claims are generated from model weights, not from retrieved evidence. Sources are often fabricated or misattributed. | Dedicated `grounding` layer normalizes evidence into `CitationRecord`s with provenance chains. Every claim must trace to an `EvidenceItem`. |
| **No verification** | The system that generates a claim is also the only system that "checks" it. There is no independent audit. | Dedicated `verification` layer, structurally separate from `deliberation`. Verification labels claims — it never modifies them. |
| **No reproducibility** | Runs are not logged, configs are not saved, results are not comparable across experiments. | `ExperimentRecord` schema, experiment templates, seed management, config snapshots. See [§12](#12-experimental-methodology). |
| **No failure analysis** | When output quality is poor, there is no mechanism to determine which component failed or why. | Typed boundaries between every layer make it possible to evaluate each layer independently. Failure taxonomy in [§14](#14-failure-modes-to-track). |

---

## 4. Proposed Architectural Direction

### Core Thesis

LLMs are powerful interpreters and synthesizers but unreliable as sole sources of truth. ASAR enforces a separation:
- **Neural** — LLM-powered reasoning, interpretation, synthesis, critique
- **Symbolic** — structured memory, knowledge graphs, typed schemas, deterministic verification

This neuro-symbolic separation is the architectural foundation. Every design decision should reinforce it.

### Layer Architecture

The system has eight layers. Each has a single responsibility, typed inputs/outputs, and can be swapped without changing adjacent layers. All inter-layer communication goes through `orchestration` — layers never import each other directly.

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

### Simplified Dataflow

v0 dataflow (grounding inactive, sequential execution):
```
Research Goal
  → planning produces ResearchPlan with sequential PlanSteps
  → orchestration creates TaskPackets, dispatches sequentially to execution
  → execution produces EvidenceItems with SourceMetadata
  → memory stores EvidenceItems
  → deliberation synthesizes evidence → DecisionPacket with Claims
  → verification checks claims against evidence → VerificationResult
  → evaluation logs run as ExperimentRecord with metrics
  → orchestration assembles ResearchOutput → writes to disk
```

Full dataflow (Phase 2+, grounding active):
```
Research Goal
  → planning produces ResearchPlan (sequential or parallel PlanSteps)
  → orchestration dispatches TaskPackets to execution (potentially parallel)
  → execution produces EvidenceItems
  → grounding normalizes evidence, builds CitationRecords
  → memory stores and compresses results
  → deliberation synthesizes across evidence, detects conflicts → DecisionPacket
  → verification checks claims against evidence and CitationRecords
  → evaluation scores the run against benchmarks
  → Final output: grounded, cited, verified ResearchOutput
```

Full dataflow diagram: [docs/architecture/dataflow.md](docs/architecture/dataflow.md)
Per-layer contracts: [docs/architecture/system-overview.md](docs/architecture/system-overview.md)
What code lives where: [docs/architecture/component-map.md](docs/architecture/component-map.md)

### Assumptions

Working assumptions. Revisit as the project matures.

1. **Python is sufficient for the prototype.** Performance-critical paths can be optimized later.
2. **Single orchestrator, single process.** Distributed orchestration is deferred to Phase 4+.
3. **LLM access via API.** No local model hosting in Phase 0–1.
4. **Text-based research only.** Multimodal support is out of scope initially.
5. **Single-machine execution.** Cluster execution is deferred.

---

## 5. Core Design Principles

These are not aspirational — they are constraints that govern every implementation decision.

1. **Separate planning from execution.** `planning` decides *what* to investigate; `execution` decides *how* to retrieve it. Neither knows about the other's internals.
2. **Separate generation from verification.** The module that produces a claim (`deliberation`) must never be the sole module that checks it (`verification`). This is invariant #4.
3. **Preserve provenance.** Every transformation — from raw web snippet to final cited claim — is traceable through `EvidenceItem` → `CitationRecord` → `Claim` chains.
4. **Reproducible experiments.** Config + seed + data = same result. If it's not reproducible, it's not research. See [§12](#12-experimental-methodology).
5. **Typed structures over vague prose.** All inter-layer data uses Pydantic models from `schemas/`. Schemas are documentation the runtime checks.
6. **Inspectable decisions.** No hidden state changes. Every `DecisionPacket` includes its reasoning trace, conflicts, and epistemic status.
7. **Swappable modules.** Code to protocols in `asar/core/protocols.py`, not to implementations. Any layer can be replaced without touching adjacent layers.
8. **Long-horizon maintainability.** This codebase will be read 100x more than written. Clarity beats cleverness.
9. **Agent-legible.** The repo must be fully understandable by a coding agent that reads the docs. No tribal knowledge, no implicit conventions.
10. **Assumptions before abstractions.** Write down *why* in [docs/architecture/decision-log.md](docs/architecture/decision-log.md) before writing *how* in code.

---

## 6. System Layers

Each layer has a canonical name (used in code, docs, commits, and config), a module path, a protocol, and a single responsibility. Detailed contracts with inputs, outputs, and per-layer invariants are in [docs/architecture/system-overview.md](docs/architecture/system-overview.md).

| # | Layer | Module | Protocol | Responsibility |
|---|-------|--------|----------|---------------|
| 1 | `planning` | `asar/planning/` | `PlannerProtocol` | Decompose a research goal into a structured `ResearchPlan` with ordered/parallel `PlanStep`s |
| 2 | `execution` | `asar/execution/` | `ExecutorProtocol` | Execute a `TaskPacket` and return `EvidenceItem`(s) — stateless, all context in the packet |
| 3 | `deliberation` | `asar/deliberation/` | `DeliberationProtocol` | Synthesize evidence into `DecisionPacket` with claims, conflicts, epistemic status |
| 4 | `memory` | `asar/memory/` | `MemoryProtocol` | Store, retrieve, and compress typed artifacts — explicit tiers: working, compressed, evicted |
| 5 | `grounding` | `asar/grounding/` | `GroundingProtocol` | Normalize `EvidenceItem`s into canonical form, produce `CitationRecord`s, track provenance |
| 6 | `verification` | `asar/verification/` | `VerificationProtocol` | Check claims against evidence, validate citations — labels only, never modifies claims |
| 7 | `evaluation` | `asar/evaluation/` | `EvaluationProtocol` | Benchmarks, metrics, experiment logging — post-hoc and deterministic |
| 8 | `orchestration` | `asar/orchestration/` | — (coordinator) | Lifecycle, dispatch, inter-layer routing — the **only** module that imports other layers |

Supporting modules (not layers):
- `core` (`asar/core/`) — Protocol definitions, base types, exceptions. Imports nothing from `asar/`.
- `common` (`asar/common/`) — Config loading, logging, ID generation. Imports only `core`.

### Import Discipline

```
orchestration → imports all layers + core + common
each layer    → imports core + common + its own schemas ONLY
core          → imports nothing from asar/
common        → imports core only
```

Layers **never** import each other. All inter-layer routing goes through `orchestration`. This is invariant #7.

---

## 7. Key Entities and Data Structures

All inter-layer data uses Pydantic models from [`schemas/`](schemas/). These are the canonical types — do not create parallel type systems.

| Entity | Schema file | Produced by | Consumed by | Purpose |
|--------|-----------|------------|-------------|---------|
| `ResearchPlan` | `schemas/research_plan.py` | `planning` | `orchestration` | Structured decomposition of a goal into `PlanStep`s |
| `PlanStep` | `schemas/research_plan.py` | `planning` | `orchestration` | A single step: description, expected output, success criteria, dependencies |
| `TaskPacket` | `schemas/task_packet.py` | `orchestration` | `execution` | Unit of work: action, query, constraints — everything an executor needs |
| `EvidenceItem` | `schemas/evidence_item.py` | `execution` | `memory`, `deliberation`, `verification` | A piece of information with `SourceMetadata`, confidence, relevance |
| `SourceMetadata` | `schemas/evidence_item.py` | `execution` | (output provenance) | Provenance: URL, title, author, access date, raw snippet |
| `CitationRecord` | `schemas/citation_record.py` | `grounding` | `verification` | Links a claim to evidence with strength label. **Phase 2** — not used in v0. |
| `DecisionPacket` | `schemas/decision_packet.py` | `deliberation` | `verification` | Synthesis output: claims, conflicts, information gaps, reasoning traces |
| `Claim` | `schemas/decision_packet.py` | `deliberation` | `verification` | A single claim with `EpistemicStatus`, supporting/contradicting evidence IDs |
| `EpistemicStatus` | `schemas/decision_packet.py` | `deliberation` | `verification` | Enum: `high_confidence`, `moderate_confidence`, `low_confidence`, `contested`, `speculative`, `unknown` |
| `VerificationResult` | `schemas/verification_result.py` | `verification` | `orchestration` (output) | Per-claim verification verdicts — separate from `DecisionPacket`, never mutates claims |
| `ClaimVerification` | `schemas/verification_result.py` | `verification` | (inside `VerificationResult`) | Verdict for a single claim: supported, unsupported, insufficient, contradicted |
| `ClaimVerdict` | `schemas/verification_result.py` | `verification` | (inside `ClaimVerification`) | Enum: `supported`, `unsupported`, `insufficient`, `contradicted` |
| `ResearchOutput` | `schemas/research_output.py` | `orchestration` | (disk artifact) | Complete output of one pipeline run — plan, evidence, decision, verification, experiment |
| `ExperimentRecord` | `schemas/experiment_record.py` | `evaluation` | `evaluation` | Full run metadata: config, seed, metrics, artifacts, timing |

### Schema Naming Convention

Schema type names are **PascalCase everywhere** — code, docs, diagrams, and prose. Do not abbreviate or introduce aliases. `EvidenceItem` is never "evidence" or "item" when precision matters.

---

## 8. Research Hypotheses

These are the falsifiable claims ASAR is designed to test. Full details, test plans, and status tracking are in [docs/research/hypotheses.md](docs/research/hypotheses.md).

| ID | Claim | Layer(s) tested | Status |
|----|-------|-----------------|--------|
| H-001 | Structured plans outperform single-pass LLM prompts on factual accuracy and completeness | `planning`, `orchestration` | untested |
| H-002 | Compressed memory retains enough signal for < 10% quality drop on downstream tasks | `memory` | untested |
| H-003 | A separate verification layer catches ≥ 30% of factual errors missed by generation | `verification` | untested |
| H-004 | Grounding all claims to `EvidenceItem`s reduces hallucination by ≥ 50% | `grounding` | untested |
| H-005 | Multi-perspective deliberation (advocate/critic) improves synthesis balance and accuracy | `deliberation` | untested |

Research agenda and thread prioritization: [docs/research/research-agenda.md](docs/research/research-agenda.md).

---

## 9. Non-Goals

Things we are explicitly NOT doing. If a proposed change serves one of these goals, it should be rejected or deferred.

- **General-purpose assistant.** ASAR is a research agent, not a chatbot.
- **Chat interface or consumer product.** No UI work in the research phase.
- **Real-time streaming.** Correctness over latency. Streaming is a Phase 4+ polish item.
- **Latency optimization.** A slower correct answer is better than a fast wrong one.
- **Training or fine-tuning LLMs.** We use LLMs via API, not build them.
- **Replacing human researchers.** The goal is augmentation — a tool, not a replacement.
- **Supporting every LLM provider.** Start with one (Anthropic), add others as needed.
- **Multimodal research.** Text only until the text pipeline is proven.

---

## 10. Invariants

These must hold across **all** future changes. Violating any invariant requires explicit justification recorded in [docs/architecture/decision-log.md](docs/architecture/decision-log.md) before implementation.

| # | Name | Rule | Enforcement |
|---|------|------|-------------|
| 1 | **Grounded output** | Every claim in final output traces to an `EvidenceItem`. No ungrounded assertions. | `verification` checks; schema requires `supporting_evidence_ids` on every `Claim` |
| 2 | **Typed boundaries** | All inter-layer communication uses Pydantic models from `schemas/`. No raw string passing. | Protocol signatures; code review |
| 3 | **Reproducible experiments** | Config + seed + data = same result. | `ExperimentRecord` schema captures all inputs; see [§12](#12-experimental-methodology) |
| 4 | **Separate generation from verification** | The module that produces a claim (`deliberation`) must not be the sole module that checks it. | Architectural separation of `deliberation` and `verification` layers |
| 5 | **Explicit memory tiers** | What is in working memory vs. compressed vs. evicted is always queryable. No hidden state. | `MemoryProtocol` interface |
| 6 | **Swappable modules** | Any layer implementation can be replaced without changing adjacent layers if the protocol contract holds. | Protocol-based dispatch in `orchestration`; no cross-layer imports |
| 7 | **Orchestration-only routing** | Layers do not import or call each other directly. All inter-layer communication goes through `orchestration`. | Import discipline (see [§6](#6-system-layers)); code review |

---

## 11. Open Questions

Things we know we don't know. Each is tracked with an ID and tagged by phase and layer. The full list with details is in [docs/research/open-questions.md](docs/research/open-questions.md).

### Architecture
- **OQ-A1** [Phase 2] `planning`/`orchestration` — After v0, should the planner return a full plan upfront or stream tasks incrementally?
- **OQ-A2** [Phase 2] `grounding` — Knowledge graph: in-memory or external DB? What schema?
- **OQ-A3** [Phase 3] `execution`/`orchestration` — Parallel executor coordination: shared memory, message passing, or event bus?
- **OQ-A4** [Phase 1] `execution`/`orchestration` — Error propagation: exceptions, result types, or error channels?

### Memory
- **OQ-M1** [Phase 2] `memory` — When compression activates after v0, what compression ratio is acceptable?
- **OQ-M2** [Phase 2] `memory` — Eviction policy: when to move from working to long-term?
- **OQ-M3** [Phase 3] `memory` — Retrieval: embedding-based, keyword, or hybrid?

### Verification
- **OQ-V1** [Phase 2] `verification` — What is "sufficient evidence"? How many independent sources?
- **OQ-V2** [Phase 2] `verification`/`deliberation` — Conflicting evidence: majority vote, confidence weighting, or escalation?
- **OQ-V3** [Phase 2] `verification` — When to mark a claim "unverifiable" and stop?

### Practical
- **OQ-P1** [Phase 1] `common` — Which LLM provider first? Fallback strategy?
- **OQ-P2** [Phase 1] `common` — API key management: env vars or secrets manager?
- **OQ-P3** [Phase 2] `execution` — Rate limiting and cost management?

---

## 12. Experimental Methodology

Every non-trivial change should be testable via an experiment. This is not optional — it's how we learn what works.

### Templates

| Template | Use when | Path |
|----------|---------|------|
| Standard experiment | Testing a hypothesis or comparing approaches | [experiments/templates/experiment_template.md](experiments/templates/experiment_template.md) |
| Ablation study | Measuring contribution of a component | [experiments/templates/ablation_template.md](experiments/templates/ablation_template.md) |
| Error analysis | Analyzing failure patterns | [experiments/templates/error_analysis_template.md](experiments/templates/error_analysis_template.md) |
| Failed direction | Recording what didn't work and why | [experiments/templates/failed_direction_template.md](experiments/templates/failed_direction_template.md) |

### Experiment Lifecycle

1. Copy template → `experiments/runs/YYYY-MM-DD_<short-name>/`
2. Fill in **all metadata before running** — hypothesis, config, seed, baseline
3. Reference hypothesis ID if applicable (e.g., H-001)
4. Run
5. Record results — especially negative results
6. Add entry to [experiments/registry/experiment_index.md](experiments/registry/experiment_index.md)
7. Update [docs/research/open-questions.md](docs/research/open-questions.md) if findings change understanding

### Reproducibility Requirements

Every experiment must record (fields match `ExperimentRecord`):
- Git commit hash
- Full config snapshot
- Model provider and model ID
- Random seed (default: 42, set in [config/experiments.toml](config/experiments.toml))
- Input data reference
- Python version and key dependency versions

Full reproducibility protocol: [docs/operations/reproducibility.md](docs/operations/reproducibility.md).

### Recording Failed Directions

When an approach fails, record it in `experiments/notes/YYYY-MM-DD_failed_<name>.md` using [failed_direction_template.md](experiments/templates/failed_direction_template.md). Include: what was tried, why it was expected to work, what happened, why it failed. The goal is not to avoid failures — it's to avoid **repeated** failures.

---

## 13. Evaluation Strategy

Evaluation is a first-class concern. Metrics must be defined before implementation, not after.

### Evaluation Dimensions

| Dimension | What it measures | Method | Layer tested |
|-----------|-----------------|--------|-------------|
| **Factual accuracy** | Are claims correct? | Human annotation + automated spot-checks | `verification` |
| **Completeness** | Does output cover key facets? | Human evaluation with topic rubric | `planning`, `execution` |
| **Groundedness** | Is every claim backed by evidence? v0: fraction of claims with verdict `SUPPORTED`. Phase 2+: backed by `CitationRecord`. | Automated check | `verification` (v0), `grounding` (Phase 2+) |
| **Citation quality** | Phase 2+: does cited evidence actually support the claim? | Human evaluation + retrieval check | `grounding`, `verification` |
| **Plan quality** | Is the `ResearchPlan` well-structured? | Human evaluation of plans | `planning` |
| **Memory fidelity** | Does compressed memory retain needed information? | Ablation: compressed vs. full context | `memory` |

### Benchmark Tiers

| Tier | Difficulty | Example | Target phase |
|------|-----------|---------|-------------|
| 1 | Simple factual | "Main causes of the 2008 financial crisis?" | Phase 1 |
| 2 | Multi-source synthesis | "Compare UBI approaches in Finland, Kenya, and Stockton" | Phase 2–3 |
| 3 | Nuanced / controversial | "Scientific consensus on long-term intermittent fasting effects?" | Phase 3 |
| 4 | Deep technical | "Transformer vs. state-space architecture tradeoffs for long context?" | Phase 4 |

Full evaluation plan: [docs/evaluation/evaluation-plan.md](docs/evaluation/evaluation-plan.md).
Benchmark details: [docs/evaluation/benchmarks.md](docs/evaluation/benchmarks.md).

---

## 14. Failure Modes to Track

These are the categories of failure we expect to encounter. Tracking them is essential for understanding where to invest improvement effort. Use [experiments/templates/error_analysis_template.md](experiments/templates/error_analysis_template.md) to analyze failures.

| ID | Failure mode | Origin layer | Description | Detection method |
|----|-------------|-------------|-------------|-----------------|
| FM-1 | **Bad decomposition** | `planning` | Plan misses key sub-questions or creates redundant steps | Human evaluation of `ResearchPlan`; task coverage metrics |
| FM-2 | **Retrieval miss** | `execution` | Executor fails to find relevant sources, or finds only irrelevant ones | Recall against known-good source sets |
| FM-3 | **Source quality failure** | `execution` | Evidence comes from unreliable or outdated sources | Source credibility scoring (future) |
| FM-4 | **Grounding failure** | `grounding` | `CitationRecord` links a claim to evidence that doesn't actually support it | Human evaluation of citation accuracy |
| FM-5 | **Synthesis distortion** | `deliberation` | Deliberation misrepresents or over-simplifies the evidence | Comparison of `DecisionPacket` claims against raw evidence |
| FM-6 | **Conflict suppression** | `deliberation` | Legitimate disagreements in evidence are silently resolved instead of preserved | Check `conflicts` field is populated when evidence disagrees |
| FM-7 | **Verification miss** | `verification` | Verification fails to flag a factual error | Error injection experiments (H-003) |
| FM-8 | **Memory information loss** | `memory` | Compression drops facts needed by downstream layers | Ablation: full vs. compressed (H-002) |
| FM-9 | **Hallucination** | `deliberation` | Claims appear in output with no supporting `EvidenceItem` | Automated groundedness check |
| FM-10 | **Premature termination** | `orchestration` | System declares "done" before sufficient evidence is gathered | Completeness metrics |
| FM-11 | **Error cascade** | `orchestration` | A failure in one layer propagates unchecked and corrupts downstream layers | Typed error handling; layer isolation |
| FM-12 | **Infinite re-planning** | `planning`/`orchestration` | Re-plan loop fails to converge | Iteration limits; termination conditions |

When analyzing a specific run's failures, classify each error by FM-ID, trace it to its origin layer, and note whether it was caught downstream. This builds the empirical basis for deciding where to invest effort.

---

## 15. Roadmap

### Phase 0 — Bootstrap (done) `[bootstrap]`
Repository structure, documentation, typed schemas, protocol definitions, experiment infrastructure.

### Phase 1 — Minimal End-to-End Pipeline `[v0]`
The frozen implementation target is one sequential end-to-end vertical slice. v0 tuning is complete for now and [v0_tier1_eval_set_004](experiments/notes/v0_tier1_eval_set_004.md) is the official live reference baseline. See [v0-canonical-architecture.md](docs/architecture/v0-canonical-architecture.md) for exact scope and success criteria.

- `SimplePlanner` (`planning`) — single LLM call, goal → `ResearchPlan` with sequential `PlanStep`s
- `WebSearchExecutor` (`execution`) — one search API call per `TaskPacket` → `list[EvidenceItem]`
- `WorkingMemory` (`memory`) — Python dict store/retrieve, `compress()` is a no-op
- `SimpleSynthesizer` (`deliberation`) — single LLM call over all evidence → `DecisionPacket` with `Claim`s
- `EvidenceChecker` (`verification`) — deterministic Python, no LLM. Checks referential integrity and keyword relevance → `VerificationResult`
- `ExperimentLogger` (`evaluation`) — builds `ExperimentRecord`, computes metrics, writes to disk
- `SequentialOrchestrator` (`orchestration`) — drives the full pipeline sequentially, assembles `ResearchOutput`
- Config loading from TOML files (`common`)
- 5 Tier 1 benchmark questions with rubrics

Supported development/runtime baseline for this phase: Python 3.11+. Any validation observed under Python 3.10.x is non-canonical.

### Phase 1.5 — Minimal Claim Selection Architecture `[v1-minimal]`
- Keep planning, execution, memory, verification, and evaluation intact
- Split current deliberation into two steps:
  - candidate claim generation
  - support-aware claim selection
- Introduce one new architectural capability only: selection/ranking after generation
- Selector priorities:
  - stronger support
  - higher question relevance
  - better non-duplication
  - sufficient specificity
- Do not add grounding, re-planning, parallelism, debate, or advanced memory in this step

See [docs/architecture/v1-minimal-architecture.md](docs/architecture/v1-minimal-architecture.md) and [tasks/v1_minimal_plan.md](tasks/v1_minimal_plan.md).

### Phase 2 — Grounding, Re-planning & Enhanced Verification
- Evidence normalization and `CitationRecord` generation (`grounding`)
- Knowledge graph (`grounding`)
- LLM-based verification — "does this evidence support this claim?" (`verification`)
- Re-planning loop based on execution feedback (`orchestration`, `planning`)
- Memory compression and eviction (`memory`)
- Embedding-based retrieval (`memory`)

### Phase 3 — Deliberation & Parallel Execution
- Multi-perspective synthesis: advocate/critic/red-team (`deliberation`)
- Conflict detection and preservation (`deliberation`)
- Parallel executor dispatch with scheduling (`execution`, `orchestration`)

### Phase 4 — Evaluation & Experimentation `[research-only]`
- Full benchmark suite across all tiers
- Ablation framework
- Error analysis tooling
- Experiment dashboard

Immediate priorities: [tasks/next_steps.md](tasks/next_steps.md).
Full backlog: [tasks/backlog.md](tasks/backlog.md).
Phase 0 completion record: [tasks/phase_00_bootstrap.md](tasks/phase_00_bootstrap.md).

---

## 16. Agent Instructions for Future Modifications

This section tells future coding agents how to reason about changes. For the full operational workflow (commands, commit format, handoff notes), see [AGENTS.md](AGENTS.md).

### Before Changing Anything

1. Read [AGENTS.md](AGENTS.md) — rules, workflows, pitfalls
2. Read this file — especially [§10 Invariants](#10-invariants) and [§5 Design Principles](#5-core-design-principles)
3. Identify which layer your change affects — see [§6](#6-system-layers) and [docs/architecture/component-map.md](docs/architecture/component-map.md)
4. Check if a schema and protocol already exist for your work — see [§7](#7-key-entities-and-data-structures) and `asar/core/protocols.py`
5. Check [docs/architecture/decision-log.md](docs/architecture/decision-log.md) for past decisions that constrain your approach
6. Check [experiments/notes/](experiments/notes/) for failed directions you should not repeat

### Reasoning Checklist

For every non-trivial change, answer these questions:

- **Which layer?** Does my change affect one layer or multiple? If multiple, am I preserving the routing-through-orchestration invariant (#7)?
- **Which schema?** Am I using canonical types from `schemas/`, or am I inventing new ones? If new types are needed, do they belong in `schemas/` as a new canonical entity?
- **Which invariant?** Does my change preserve all seven invariants? If not, which one breaks and is there a justification?
- **How to evaluate?** How would we know if this change is an improvement? Can it be tested with an experiment? Does it affect a hypothesis?
- **What to document?** Which docs need updating? (See documentation update matrix in [AGENTS.md](AGENTS.md).)
- **What could go wrong?** Does this change introduce a new failure mode from [§14](#14-failure-modes-to-track)?

### What Not to Change Without a Decision Record

Some artifacts are load-bearing — changing them has cascading effects. See [AGENTS.md § What Not to Change Casually](AGENTS.md#what-not-to-change-casually) for the full list. The short version: do not modify `schemas/`, `asar/core/protocols.py`, or this section (§10 Invariants) without first recording a decision in [docs/architecture/decision-log.md](docs/architecture/decision-log.md).

---

## 17. Glossary

Terms used across the project. Schema type names are **PascalCase** everywhere.

| Term | Definition | Where defined |
|------|-----------|--------------|
| `Claim` | A single assertion with epistemic status and evidence links | `schemas/decision_packet.py` |
| `CitationRecord` | A link between a claim and its supporting/contradicting evidence, with strength label | `schemas/citation_record.py` |
| `CitationStrength` | Enum: `strong`, `moderate`, `weak`, `contradicts` | `schemas/citation_record.py` |
| `DecisionPacket` | Output of deliberation: claims, conflicts, synthesis, information gaps | `schemas/decision_packet.py` |
| `EpistemicStatus` | Enum: `high_confidence`, `moderate_confidence`, `low_confidence`, `contested`, `speculative`, `unknown` | `schemas/decision_packet.py` |
| `EvidenceItem` | A piece of information with source metadata, confidence, and relevance scores | `schemas/evidence_item.py` |
| `ClaimVerdict` | Enum: `supported`, `unsupported`, `insufficient`, `contradicted` | `schemas/verification_result.py` |
| `ClaimVerification` | Verdict for a single claim — result of checking one `Claim` against evidence | `schemas/verification_result.py` |
| `ExperimentRecord` | Full metadata and results for one experiment run | `schemas/experiment_record.py` |
| `PlanStep` | A single step within a `ResearchPlan`: description, expected output, success criteria, dependencies | `schemas/research_plan.py` |
| `ResearchOutput` | Complete output of one pipeline run — plan, evidence, decision, verification, experiment | `schemas/research_output.py` |
| `ResearchPlan` | Structured decomposition of a research goal into ordered/parallel `PlanStep`s | `schemas/research_plan.py` |
| `SourceMetadata` | Provenance: source type, URL, title, author, access date, raw snippet | `schemas/evidence_item.py` |
| `SourceType` | Enum: `web_search`, `document`, `api`, `database`, `user_input`, `llm_generated` | `schemas/evidence_item.py` |
| `TaskPacket` | Unit of work dispatched to an executor: action, query, constraints — everything needed to execute | `schemas/task_packet.py` |
| `TaskStatus` | Enum: `pending`, `running`, `completed`, `failed`, `skipped` | `schemas/task_packet.py` |
| `VerificationResult` | Aggregate verification output for a `DecisionPacket` — contains per-claim verdicts | `schemas/verification_result.py` |
| **Grounding** | The process of linking generated claims to verifiable evidence with provenance. Phase 2 — not active in v0. | conceptual; implemented in `asar/grounding/` |
| **Invariant** | A rule that must hold across all future changes — see [§10](#10-invariants) | this document |
| **Layer** | One of the eight architectural modules — see [§6](#6-system-layers) | this document |
| **Provenance** | The chain of transformations from raw source to final claim. In v0, tracked via `SourceMetadata` → `EvidenceItem` → `Claim`. In Phase 2+, also via `CitationRecord`. | conceptual; tracked in `schemas/` |
| **Protocol** | A Python Protocol defining a layer's interface contract | `asar/core/protocols.py` |
