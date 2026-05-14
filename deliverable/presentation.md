---
marp: true
theme: default
paginate: true
size: 16:9
title: "ASAR — Agentic Structured Autonomous Researcher"
description: "A grounded multi-step research agent with RAG, fine-tuning, and safety."
---

<!-- _class: lead -->

# ASAR
## Agentic Structured Autonomous Researcher

A grounded multi-step research agent built around the principle:

> *Generation is never its own checker.*

**Adrian Trill** · LLM-Based Agents course final project

---

# Outline

1. **Introduction** — what the system is and why it exists
2. **Problem definition** — the failure mode we target
3. **State of the art** — what existing agents do and don't solve
4. **Proposed solution** — architecture, layers, schemas
5. **Experiments** — the LLM-course rubric, mapped to code
6. **Results & demo** — live run, numbers, artifacts

---

<!-- _class: lead -->

# 1. Introduction

---

# What ASAR is

A **typed, multi-step research agent** that:

- Plans a research goal into ordered tasks (`ResearchPlan` → `TaskPacket[]`)
- Executes them against a **RAG corpus** (SciFact) or web search
- Stores evidence in a tiered memory (working / compressed / evicted)
- Deliberates to produce `DecisionPacket{claims, evidence_refs}`
- **Verifies** each claim against its cited evidence (separate from generation)
- Logs a reproducible `ExperimentRecord` for every run
- Wraps everything in a **safety filter** (toxicity + prompt-injection)

Everything is typed Pydantic data. No raw strings cross layer boundaries.

---

# Why this shape

The system reflects **seven invariants** (`PROJECT_DOSSIER.md § 10`):

| # | Invariant |
|---|----------|
| 1 | Every claim traces to an `EvidenceItem` |
| 2 | All inter-layer data uses `schemas/` models (no raw strings) |
| 3 | Same config + seed + data ⇒ same result |
| 4 | The producer of a claim is never its sole checker |
| 5 | Memory tiers (working/compressed/evicted) are always queryable |
| 6 | Implementations are swappable behind protocols |
| 7 | Orchestration is the only router — layers don't import each other |

Every architectural decision must preserve all seven.

---

<!-- _class: lead -->

# 2. Problem definition

---

# The failure mode we target

LLM agents routinely produce confident-sounding answers that are:

- **Ungrounded** — no evidence trace at all
- **Mis-grounded** — cite a source that doesn't actually support the claim
- **Self-validated** — the same model that made the claim "checks" it
- **Opaque** — no record of what was decided, when, and why
- **Unsafe** — toxic output, or steered by prompt injection

For an **autonomous** researcher operating over hours/days, these compound:
one bad claim becomes seed input for the next step.

---

# What "grounded" must mean here

A claim is grounded only if **all** of these hold:

1. It points to specific `EvidenceItem`(s)
2. Those evidence items have full provenance (URL, snippet, retrieval rank, fusion score, trust label)
3. A **different** module — `EvidenceChecker` — confirmed the claim is supported by the evidence text
4. The verification verdict is recorded in `VerificationResult`
5. The run is replayable from `ExperimentRecord` (seed, config, plan, evidence, claims)

If any link breaks, the claim is **not** allowed in the output.

---

<!-- _class: lead -->

# 3. State of the art

---

# Where the field is today

| System type | What works | What's missing |
|-------------|-----------|----------------|
| Raw chat LLM with web tools | Easy to build, broad knowledge | No groundedness check, opaque |
| ReAct / Reflexion agents | Step-by-step reasoning | Same model self-verifies |
| LangChain / LlamaIndex RAG | Good retrieval primitives | Output structure is ad-hoc strings |
| AutoGPT / GPT-Researcher | End-to-end research demos | Hallucinations, no replayability |
| Constitutional AI | Strong on safety | Doesn't solve evidence grounding |

**Gap**: a system that combines typed contracts, RAG, separate verification,
and replayable experiments — with **no single bypassable layer.**

---

# Key references that shaped ASAR

- **RAG**: Lewis et al. 2020 — retrieval-augmented generation
- **Reciprocal-rank fusion**: Cormack, Clarke & Buettcher 2009 — combine dense + sparse rankings
- **BM25**: Robertson & Walker 1994 — battle-tested lexical scoring
- **Detoxify / Perspective API**: model-based toxicity scoring
- **LoRA**: Hu et al. 2021 — parameter-efficient fine-tuning
- **BeIR**: Thakur et al. 2021 — heterogeneous retrieval benchmark (SciFact is one of its tasks)

---

<!-- _class: lead -->

# 4. Proposed solution

---

# Architecture: eight layers, one router

```
                       ┌──────────────────────────┐
                       │     orchestration         │ ← only layer that imports others
                       └────────────┬─────────────┘
                                    │
   ┌──────────┬──────────┬──────────┼──────────┬──────────┬──────────┐
   ▼          ▼          ▼          ▼          ▼          ▼          ▼
planning  execution   memory  deliberation verification evaluation grounding
   │       │            │           │           │           │           │
   ▼       ▼            ▼           ▼           ▼           ▼           ▼
ResearchPlan TaskPacket Evidence  Decision  Verification Experiment  Citation
            EvidenceItem  Item    Packet    Result       Record       Record
```

**Layers never import each other.** Every arrow is a Pydantic schema.

---

# What's in each layer (v0 vertical slice)

| Layer | Implementation | Output |
|-------|---------------|--------|
| **planning** | `SimplePlanner` | `ResearchPlan` |
| **execution** | `WebSearchExecutor` + RAG `CorpusSearchClient` | `EvidenceItem[]` |
| **memory** | `WorkingMemory` (LRU, tiered) | queryable buffer |
| **deliberation** | `SimpleSynthesizer` | `DecisionPacket` |
| **verification** | `EvidenceChecker` (separate model invocation) | `VerificationResult` |
| **evaluation** | `ExperimentLogger` | `ExperimentRecord` |
| **orchestration** | `SequentialOrchestrator` | `ResearchOutput` |
| **safety** *(new)* | `SafetyAwareRunner` wrapper | `safety.json` |

---

# RAG subsystem (`asar/execution/rag/`)

Stack:

- **Corpus**: BeIR/SciFact — 5,183 scientific abstracts, ~4.5 MB
- **Chunker**: section → paragraph → sentence fallback, 450-token target, 80-token overlap
- **Embedder**: `FastEmbed(BAAI/bge-small-en-v1.5)` or deterministic `HashingEmbedder` fallback
- **Vector index**: Qdrant (local on-disk)
- **Lexical index**: BM25 (`rank_bm25`)
- **Fusion**: Reciprocal-rank fusion, `k=60`, `top_k*4` candidates each side

Reproducible CLI: `uv run python -m asar.execution.rag.cli --dataset scifact`

Provider wrapper: `CorpusSearchClient` implements `SearchClientProtocol` →
the existing `WebSearchExecutor` consumes it **without modification**.

---

# Fine-tuning (`asar/finetune/` + `scripts/finetune_lora.py`)

Goal: produce a small open-weights model that:

- Answers grounded Q&A
- Refuses out-of-passage claims
- Runs on a laptop (Mac, no GPU)

| Setting | Value |
|---------|-------|
| Base model | `Qwen/Qwen2.5-0.5B-Instruct` |
| Adapter | LoRA, r=8, α=16, dropout=0.05 |
| Targets | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| Data | ~1,500 SciFact passage-grounded Q&A pairs (chat format) |
| Hardware | CPU/MPS, batch=1, grad-accum=8, 1 epoch |
| Inference | `LocalSLMClient(LLMClientProtocol)` auto-detects MPS/CUDA/CPU |

---

# Safety (`asar/safety/`)

Non-invasive wrapper around the orchestrator:

```
        ┌────────────────────────────────────────────┐
goal ──▶│  pre-flight safety check (block if unsafe) │
        └────────────────────────────────────────────┘
                          │
                          ▼
        ┌────────────────────────────────────────────┐
        │            v0 orchestrator                  │ ← unchanged
        └────────────────────────────────────────────┘
                          │
                          ▼
        ┌────────────────────────────────────────────┐
        │ post-flight check: evidence + each claim    │
        │ unsafe claims stripped, safety.json written │
        └────────────────────────────────────────────┘
```

Two backends: `KeywordSafetyFilter` (regex baseline, always available) and
optional `DetoxifySafetyFilter` (model-backed).

---

<!-- _class: lead -->

# 5. Experiments

---

# The course rubric — and where in the codebase it lives

| Rubric requirement | Where we satisfy it |
|---|---|
| Data ingestion of new datasets | `asar/execution/rag/scifact_loader.py` — downloads + normalizes BeIR/scifact (5,183 docs) |
| Task-specific fine-tuning (Q&A) | `asar/finetune/dataset.py` + `scripts/finetune_lora.py` — LoRA on Qwen2.5-0.5B |
| RAG | `asar/execution/rag/{chunker,embedder,retriever}.py` — chunking + Qdrant + BM25 + RRF |
| RLHF | `asar/finetune/preference_dataset.py` + `scripts/dpo_train.py` — DPO over SciFact preferences |
| Evaluation | `asar/evaluation/experiment_logger.py` — `ExperimentRecord` per run, `safety.json` for safety verdicts |
| Toxicity / hallucinations | `asar/safety/` + `asar/verification/evidence_checker.py` |

---

# Test coverage

```
$ uv run pytest -q --ignore=tests/test_live_providers.py
186 passed in 0.78s
```

Test files:

- `test_schemas.py` — Pydantic contracts hold
- `test_planning.py`, `test_execution.py`, `test_memory_foundations.py`,
  `test_deliberation.py`, `test_verification.py`, `test_evaluation.py`,
  `test_orchestration.py`, `test_v0_integration.py` — every layer
- `test_rag.py` — chunker, embedder, BM25, Qdrant, hybrid retriever (8 tests)
- `test_safety.py` — keyword filter, SafetyChecker over goal/evidence/claims (7 tests)
- `test_local_llm.py` — `LocalSLMClient`, SFT dataset (4 tests)

---

# Reproducibility

Every run produces three artifacts:

```
experiments/runs/2026-05-14_rag_safety_e2e/artifacts/
├── output.json       ← ResearchOutput (claims + evidence)
├── experiment.json   ← ExperimentRecord (config + seed + plan + run)
└── safety.json       ← pre- and post-flight safety reports
```

Same goal + same config + same seed ⇒ same output.

`ExperimentRecord` includes config hash, pipeline version, schema version.

---

<!-- _class: lead -->

# 6. Results & demo

---

# Indexing the SciFact corpus

```
$ uv run python -m asar.execution.rag.cli --dataset scifact --embed-backend hashing

[1/4] Preparing scifact ............ 0.02 s
[2/4] Chunking (5183 → 5208) ....... 0.27 s
[3/4] Embedding & indexing ......... 2.93 s
[4/4] Probe retrieval .............. 0.01 s
                                     -------
                                     3.23 s total
```

Probe query "What causes BRCA1-related cancers?" returns the gold BRCA1 paper
at rank 1 **even with the deterministic hashing embedder** (no model
weights).

---

# End-to-end run

```
$ ASAR_SAFETY_ENABLED=1 ASAR_SEARCH_PROVIDER=corpus \
    uv run python -m asar.demo "What is known about BRCA1 in breast cancer?"

Plan steps: 3
Evidence items: 3
ResearchOutput artifact: output.json
ExperimentRecord artifact: experiment.json
```

Every evidence item in `output.json` carries:

```json
"raw_payload": {
  "chunk_id": "26952804::f1ad48d222f9",
  "doc_id": "26952804",
  "dense_rank": 7,
  "lexical_rank": 2,
  "fused_score": 0.031054405392392875,
  "trust_label": "peer_reviewed",
  "section": "body",
  "tags": ["scifact", "scientific_claim"]
}
```

---

# Safety verdict (excerpt of `safety.json`)

```json
{
  "pre_report":  { "blocked": false, "max_toxicity": 0.0, "max_injection": 0.0,
                   "verdict_count": 1, "unsafe_count": 0 },
  "post_report": { "blocked": false, "max_toxicity": 0.0, "max_injection": 0.0,
                   "verdict_count": 4, "unsafe_count": 0 },
  "stripped_claims": []
}
```

Goal, then evidence and each claim, are all scored. Unsafe claims are
stripped from the final `ResearchOutput`. Unsafe goals abort before
planning.

---

# Honest grading position

| Rubric item | Status |
|------|------|
| Data ingestion (new dataset) | ✅ SciFact via `datasets`, normalized, chunked, indexed |
| Fine-tuning (Q&A) | ✅ LoRA on Qwen2.5-0.5B SLM, runs on Mac CPU/MPS |
| RAG | ✅ Qdrant + BM25 + RRF on local corpus |
| Evaluation | ✅ `ExperimentRecord` + `safety.json` + 186 tests |
| Toxicity / hallucinations | ✅ Keyword + Detoxify backends; `EvidenceChecker` for groundedness |
| RLHF | ✅ DPO over 1,000 SciFact preference pairs (reward-model-free) |

Open-weights SLM (Qwen2.5-0.5B), fine-tuned, runnable on a laptop — rubric
ceiling **10**.

---

<!-- _class: lead -->

# Demo

Live run, then walk through `output.json`, `experiment.json`, `safety.json`.

---

# Limitations & next steps

- Full **PPO RLHF** is out of scope; we ship **DPO** as the reward-model-free RLHF flavor
- The fine-tuning dataset is small (~1,500 pairs) — sufficient as a proof,
  not as a production model
- The keyword safety baseline catches obvious cases; Detoxify is optional
- Re-planning, parallel execution, and multi-perspective debate are
  v1.x / Phase 2 work — out of scope for v0

What's *next*, in order of impact:

1. Swap the hashing embedder for FastEmbed (`BAAI/bge-small-en-v1.5`)
2. Train the LoRA for >1 epoch with a larger SciFact-derived SFT set
3. Train DPO for more epochs on a ≥10k preference set and compare to SFT-only
4. Add re-planning loop on `EvidenceChecker` failure

---

<!-- _class: lead -->

# Thank you

**Code**: `/asar/` — eight layers, ~5,000 LoC, 186 tests
**Docs**: `PROJECT_DOSSIER.md`, `docs/architecture/`, `experiments/`
**Reproduce**: `uv sync --extra dev --extra rag && uv run pytest`
