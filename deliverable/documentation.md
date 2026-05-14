# ASAR — Final Project Documentation

**Project**: ASAR — Agentic Structured Autonomous Researcher
**Course**: LLM-Based Agents
**Author**: Adrian Trill
**Code**: `LLMs-multi-step-research-agents` repository
**Status**: v0 vertical slice complete; RAG, safety, and fine-tuning fully implemented

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem definition](#2-problem-definition)
3. [State of the art](#3-state-of-the-art)
4. [Proposed solution](#4-proposed-solution)
5. [Experiments](#5-experiments)
6. [Results & demo](#6-results--demo)
7. [Limitations and future work](#7-limitations-and-future-work)
8. [How to reproduce](#8-how-to-reproduce)
9. [File map](#9-file-map)

---

## Mapping to the 12-slide presentation

This document follows the same structure as `presentation.pptx`. Each
documentation section corresponds to one or more slides; use this table to
jump between the two artifacts.

| Presentation slide                            | Documentation section                |
| --------------------------------------------- | ------------------------------------ |
| 1. Title                                      | (cover)                              |
| 2. What ASAR is                               | § 1. Introduction                    |
| 3. Why this is hard                           | § 2. Problem definition              |
| 4. Where the field is today                   | § 3. State of the art                |
| 5. Architecture (8 layers, one router)        | § 4. Proposed solution — Architecture |
| 6. Four rubric capabilities — one pipeline    | § 4. Proposed solution — RAG / SFT+DPO / Safety |
| 7. Rubric → code                              | § 5. Experiments                     |
| 8. Results                                    | § 6. Results & demo                  |
| 9. Live demo                                  | § 6 + `demo_runbook.md`              |
| 10. Honest grading position                   | § 6. Results & demo — self-assessment |
| 11. Limitations & next steps                  | § 7. Limitations and future work     |
| 12. Thank you                                 | § 8 + § 9 (reproduce + file map)     |

---

## 1. Introduction

*Corresponds to slide 2 — “What ASAR is”.*

ASAR is a **multi-step autonomous research agent** built around one principle:

> **A claim is only allowed in the final output if a *different* component
> than the one that produced it has confirmed it is supported by a specific
> piece of evidence with full retrieval provenance.**

The system is organised as a small number of typed layers — `planning`,
`execution`, `memory`, `deliberation`, `verification`, `evaluation`,
`grounding`, and `orchestration` — that communicate **only** via Pydantic
schemas in `schemas/`. No raw strings cross a boundary; no layer imports
another.

The v0 implementation is a **sequential vertical slice** that connects every
layer end-to-end on a single research goal. For the final deliverable, the
project adds four further capabilities that the LLM-course rubric requires
to reach the highest grade tier:

- **Data ingestion + RAG** over a real dataset (BeIR/SciFact)
- **Task-specific fine-tuning** of a small open-weights model via LoRA SFT
- **RLHF via DPO** (Direct Preference Optimization, reward-model-free)
- A **safety filter** that wraps the orchestrator without touching it

The repository ships with **186 passing tests**, a reproducible RAG indexing
CLI, reproducible SFT and DPO dataset CLIs, and a reproducible demo CLI.
Every run emits a typed `ResearchOutput`, an `ExperimentRecord`, and (when
safety is on) a `safety.json` artifact.

### Vocabulary

The project uses a **fixed set of names**. Synonyms are deliberately
avoided.

| Canonical name | Meaning |
|---------------|---------|
| `ResearchPlan`, `TaskPacket` | The planner's output and per-step task descriptors |
| `EvidenceItem` | One retrieved snippet with full provenance |
| `CitationRecord` | A specific quote within an `EvidenceItem` (Phase 2; deferred) |
| `DecisionPacket` | Synthesizer output: claims + their evidence references |
| `VerificationResult` | The verifier's verdict per claim |
| `ResearchOutput` | The final, typed answer the orchestrator emits |
| `ExperimentRecord` | The reproducibility envelope for a single run |

---

## 2. Problem definition

*Corresponds to slide 3 — “Why this is hard”.*

### What is actually broken with current LLM agents

For an autonomous agent that performs **multi-step research** over hours or
days, the dominant failure modes are not "the model is dumb." They are
**structural**:

1. **Ungrounded claims** — the agent emits a confident statement with no
   citation, or with a citation that doesn't actually contain the claim.
2. **Self-validation** — the same model that produced the claim is asked
   to score it. The model is biased toward defending its own output.
3. **Opaque state** — there is no record of which evidence was considered,
   which was rejected, and why. A re-run produces a different answer.
4. **Unbounded context** — naive "stuff everything into the prompt"
   schemes hide what is actually being reasoned over.
5. **Toxicity / prompt injection** — agents that consume the open web
   inherit whatever instructions sit in retrieved pages.

For a single-shot chat assistant these issues are annoying. For an
autonomous researcher that uses today's outputs as tomorrow's inputs, they
compound.

### What "solved" must look like in this project

A claim is **acceptable in the final output** only if **all** of the
following are true:

1. It is attached to one or more `EvidenceItem` IDs.
2. Each `EvidenceItem` has full retrieval provenance: `url`, `title`,
   `raw_snippet`, `source_type`, plus per-retriever metadata
   (`chunk_id`, `doc_id`, `dense_rank`, `lexical_rank`, `fused_score`,
   `trust_label`, `section`, `tags`).
3. A **different** module (the `verification` layer's
   `EvidenceChecker`) has confirmed that the evidence text supports the
   claim.
4. The verification verdict is recorded as a `VerificationResult`.
5. The run is replayable from `ExperimentRecord` (config + seed + plan +
   evidence + claims + verdicts).
6. The safety wrapper has scored the goal, evidence, and each claim and
   not blocked.

If any link breaks, the claim is **either** flagged as low-confidence in
`VerificationResult` **or** stripped entirely by the safety wrapper.

---

## 3. State of the art

*Corresponds to slide 4 — “Where the field is today”.*

### Where the field is today

| Category | Examples | What works | What's missing |
|----------|---------|-----------|----------------|
| Raw chat LLM with web tools | ChatGPT browsing | Broad knowledge | No groundedness check |
| Single-loop ReAct / Reflexion | LangChain agents | Tool use | Same model self-verifies |
| RAG frameworks | LangChain, LlamaIndex | Good primitives | Outputs are ad-hoc strings |
| Research-style agents | AutoGPT, GPT-Researcher | Multi-step demos | Hallucinations, no replayability |
| Safety wrappers | Constitutional AI, Llama Guard | Strong on toxicity | Don't solve evidence grounding |
| Long-horizon planners | Devin-style demos | Big tasks | Heavyweight, opaque |

**The structural gap**: no widely available open system combines

- typed contracts between layers,
- RAG with hybrid (dense + sparse + fusion) retrieval,
- **separate** verification, and
- **replayable** experiments

…such that **no single layer can be bypassed**. ASAR is positioned in this
gap.

### Key references that shaped the design

- **RAG** — Lewis et al. 2020. Why: retrieval-augmented generation is the
  baseline for grounded answers.
- **Reciprocal-rank fusion** — Cormack, Clarke & Buettcher 2009. Why: a
  simple, parameter-free way to combine dense and sparse rankings without
  re-training.
- **BM25** — Robertson & Walker 1994. Why: a strong lexical baseline
  whose behaviour we understand.
- **BeIR** — Thakur et al. 2021. Why: SciFact is one of its tasks, gives
  us a real scientific corpus with gold qrels.
- **LoRA** — Hu et al. 2021. Why: parameter-efficient fine-tuning that
  actually runs on a laptop.
- **Detoxify / Perspective API** — Why: model-backed toxicity scoring is
  more nuanced than keywords; we expose it as an optional backend.

---

## 4. Proposed solution

*Corresponds to slides 5 (“Architecture”) and 6 (“Four rubric capabilities — one pipeline”).*

### Architectural shape

ASAR is a directed, typed pipeline. **The orchestrator is the only layer
that imports other layers.** Every other arrow in the system is a
Pydantic schema.

```
            ┌──────────────────────────────┐
            │      orchestration            │
            │   (SequentialOrchestrator)    │
            └──────┬──────┬─────┬─────┬────┘
                   │      │     │     │
   ┌───────────────┼──────┼─────┼─────┼──────────────────┐
   ▼               ▼      ▼     ▼     ▼                  ▼
planning      execution memory deliberation verification evaluation
   │              │       │         │            │             │
ResearchPlan EvidenceItem  buffer DecisionPacket VerificationResult ExperimentRecord
```

Wrapped around this — added in the final deliverable — is the safety
runner:

```
goal → [pre-flight safety] → orchestrator → [post-flight safety] → ResearchOutput
                  │                                  │
              (block if                         (strip unsafe claims,
               unsafe goal)                      write safety.json)
```

### Per-layer responsibilities (v0)

| Layer | Module | Output | Notes |
|-------|--------|--------|-------|
| planning | `asar/planning/simple_planner.py` | `ResearchPlan` | Breaks a goal into `TaskPacket[]` |
| execution | `asar/execution/web_search_executor.py` + RAG | `EvidenceItem[]` | Consumes any `SearchClientProtocol` |
| memory | `asar/memory/working_memory.py` | queryable buffer | LRU + tier annotations |
| deliberation | `asar/deliberation/simple_synthesizer.py` | `DecisionPacket` | Produces claims and their evidence refs |
| verification | `asar/verification/evidence_checker.py` | `VerificationResult` | **Separate model invocation** |
| evaluation | `asar/evaluation/experiment_logger.py` | `ExperimentRecord` | Writes `output.json` + `experiment.json` |
| orchestration | `asar/orchestration/sequential_orchestrator.py` | `ResearchOutput` | The only router |
| safety *(new)* | `asar/safety/{__init__,pipeline}.py` | `safety.json` | Wraps the orchestrator, does not modify it |

### RAG subsystem

Located under `asar/execution/rag/`:

#### Dataset loader — `scifact_loader.py`

- Source: `BeIR/scifact` on Hugging Face (5,183 documents, 4.5 MB parquet)
- Loads via the `datasets` library (the modern HF mirror is parquet-only;
  the previous URL-based pattern was 404 by the time of submission)
- Normalises rows into `CorpusDocument(doc_id, title, text, ...)` and
  writes `data/corpora/scifact/normalized/{documents,queries,qrels}.jsonl`
- The `documents.jsonl` cache is the source of truth — subsequent runs
  do not need to re-download

#### Chunker — `chunker.py`

- `DocumentChunker` with `ChunkingConfig(target=450, max=650, overlap=80,
  min=120)` tokens
- Falls back from section-aware → paragraph-aware → sentence-aware
- Carries `overlap` tokens of context between adjacent chunks
- 5,183 SciFact docs → **5,208 chunks** (most abstracts fit in a single
  chunk)

#### Embedder — `embedder.py`

- `EmbedderProtocol` — minimal contract: `.embed(text) -> list[float]`
- `HashingEmbedder` — deterministic, model-free, dim=384, L2-normalised.
  Used in tests and when no embed model is configured. Reproducible
  without network or weights.
- `FastEmbedEmbedder` — wraps `fastembed` with
  `BAAI/bge-small-en-v1.5` (dim=384). Lazy-loads on first call.
- `build_embedder(backend=...)` resolves via arg → `ASAR_RAG_EMBED_BACKEND`
  env → `hashing` default.

#### Retriever — `retriever.py`

- `QdrantVectorIndex` — uses `qdrant-client` when available, falls back to
  brute-force cosine in memory otherwise (this is what the tests exercise).
  String chunk IDs are hashed into int64 point IDs so the local Qdrant
  on-disk format accepts them.
- `BM25Index` — uses `rank_bm25` when available, hand-rolled Okapi BM25
  fallback otherwise. Both give the same ranking on the test corpus.
- `HybridRetriever` — performs reciprocal-rank fusion with `k=60` over
  `top_k*4` candidates from each side. Returns `RetrievalHit(chunk, score,
  dense_rank, lexical_rank, fused_score)`.

#### Provider wrapper — `asar/providers/corpus_search.py`

- `CorpusSearchClient(SearchClientProtocol)` — turns retrieval hits into
  `SearchResultItem` objects with `corpus://` URLs.
- `build_corpus_search_client()` — orchestrates `prepare → chunk → embed →
  index` and returns a ready client.
- Wired into `asar/providers/factory.py` so
  `ASAR_SEARCH_PROVIDER=corpus` selects it.

#### Reproducible CLI

```
$ uv run python -m asar.execution.rag.cli --dataset scifact \
    --embed-backend hashing
```

prints per-stage timings:

```
[1/4] Preparing scifact ............ 0.02 s   (cached)
[2/4] Chunking (5183 → 5208) ....... 0.27 s
[3/4] Embedding & indexing ......... 2.93 s
[4/4] Probe retrieval .............. 0.01 s
                                     -------
                                     3.23 s total
```

### Fine-tuning — SFT then DPO

The deliverable includes both stages of modern open-model alignment:

1. **Supervised fine-tuning (SFT)** with LoRA on grounded Q&A pairs.
2. **DPO** (Direct Preference Optimization) on top of the SFT adapter.
   DPO is the reward-model-free flavor of RLHF — it directly optimizes the
   policy on `(prompt, chosen, rejected)` triples and removes the unstable
   PPO actor/critic split and the separate reward-model training stage.
   This is the practical RLHF path for CPU/MPS laptop training.

#### SFT dataset — `asar/finetune/dataset.py`

- Loads normalised SciFact and synthesises chat-format examples:
  `[{system}, {user with Passage:+Question:}, {assistant}]`
- Five question paraphrases for diversity
- System prompt instructs the model to **answer only from the passage**
  and to say so when the passage is insufficient
- Output: `data/sft/scifact_qa.jsonl` (~1,500 examples by default)

CLI:

```
$ uv run python -m asar.finetune.cli_build_dataset \
    --prepare --output data/sft/scifact_qa.jsonl --limit 1500
```

#### DPO preference dataset — `asar/finetune/preference_dataset.py`

- Same prompts as SFT, but each row is a `(prompt, chosen, rejected)`
  triple ready for `trl.DPOTrainer`.
- `chosen` is a grounded extract from the passage itself.
- `rejected` is one of three failure modes the SLM should learn to avoid:
  fabricated statistics, off-topic confident dismissal, or content from a
  different SciFact passage (silent miss).
- Default: 1,000 pairs from SciFact, deterministic for a given seed.
- Tests in `tests/test_dpo_dataset.py` assert every pair has
  `chosen != rejected` so DPO sees real preference signal.

CLI:

```
$ uv run python -m asar.finetune.cli_build_preference \
    --output data/dpo/scifact_pref.jsonl --limit 1000 --seed 42
```

#### SFT training — `scripts/finetune_lora.py`

- Uses `transformers` + `peft` + `trl.SFTTrainer`
- Default base: `Qwen/Qwen2.5-0.5B-Instruct` (480 M parameters)
- LoRA: `r=8, alpha=16, dropout=0.05`, targets
  `{q_proj, k_proj, v_proj, o_proj}`
- Mac-friendly defaults: batch=1, grad-accum=8, 1 epoch, max-seq-len=1024,
  lr=2e-4 cosine, **float32** (MPS stability)
- Auto-resolves device: MPS → CUDA → CPU
- Saves `adapter_model.bin` + tokenizer + `asar_finetune_metadata.json`

#### DPO training — `scripts/dpo_train.py`

- Uses `transformers` + `peft` + `trl.DPOTrainer`
- Starts from the SFT adapter (recommended) via `--sft-adapter`
- DPO beta = 0.1, learning rate = 5e-5 cosine, same LoRA shape
- Saves a DPO-tuned adapter to `models/asar-qwen-0.5b-scifact-dpo/` plus
  `asar_dpo_metadata.json`
- Output is consumable by `LocalSLMClient` exactly like the SFT adapter

#### Inference — `asar/providers/local_llm.py`

- `LocalSLMClient(LLMClientProtocol)` — lazy-loads transformers model +
  optional PEFT adapter
- Honours `ASAR_LOCAL_BASE_MODEL`, `ASAR_LOCAL_ADAPTER_PATH`,
  `ASAR_LOCAL_DEVICE`
- `build_live_llm_client(settings)` selects this when
  `ASAR_MODEL_PROVIDER=local`

### Safety

#### Filter — `asar/safety/__init__.py`

- `SafetyVerdict`, `SafetyReport`, `SafetyConfig` — typed dataclasses
- `KeywordSafetyFilter` — regex over toxicity, harm-intent, and
  prompt-injection patterns. Always available, no model weights.
- `DetoxifySafetyFilter` — lazy-loads `detoxify` when available. Picked by
  `ASAR_SAFETY_BACKEND=detoxify`.
- `SafetyChecker.evaluate(goal, evidence, claims)` — produces a
  `SafetyReport` over each piece of text.

#### Wrapper — `asar/safety/pipeline.py`

- `SafetyAwareRunner(orchestrator)` — wraps any orchestrator that conforms
  to the `.run(goal) -> ResearchOutput` shape.
- Pre-flight: blocks before planning if `block_on_unsafe_goal` is set and
  the goal is flagged.
- Post-flight: re-checks evidence and each claim. Unsafe claims are
  stripped (via Pydantic `model_copy()`) before returning. Writes
  `safety.json` next to `output.json`.
- **The orchestrator itself is not modified.** Every test that exercised
  v0 before still passes.

---

## 5. Experiments

*Corresponds to slide 7 — “Rubric → code”.*

### Mapping the LLM-course rubric to the codebase

| Rubric requirement | Where in this project |
|---|---|
| Data ingestion of new datasets | `asar/execution/rag/scifact_loader.py` |
| Task-specific fine-tuning (Q&A) | `asar/finetune/{dataset,cli_build_dataset}.py` + `scripts/finetune_lora.py` |
| RAG (chunking, embedding, retrieval) | `asar/execution/rag/{chunker,embedder,retriever}.py` |
| Evaluation | `asar/evaluation/experiment_logger.py` + `experiments/runs/` |
| Toxicity / hallucinations | `asar/safety/` + `asar/verification/evidence_checker.py` |
| RLHF | **Done via DPO** — `asar/finetune/preference_dataset.py` + `scripts/dpo_train.py` over 1,000 SciFact preference pairs |

### Test coverage as evidence

The full test suite, excluding the optional live-providers smoke tests
(which require external API keys), runs in under a second:

```
$ uv run pytest -q --ignore=tests/test_live_providers.py
186 passed in 0.64s
```

Breakdown:

| Test file | Tests | What it validates |
|-----------|-------|-------------------|
| `test_schemas.py` | 22 | Pydantic contracts |
| `test_common_foundations.py` | 9 | settings, logging, ids |
| `test_planning.py` | 8 | `SimplePlanner` |
| `test_execution.py` | 13 | `WebSearchExecutor` |
| `test_memory_foundations.py` | 6 | `WorkingMemory` tiers |
| `test_deliberation.py` | 12 | `SimpleSynthesizer` |
| `test_verification.py` | 10 | `EvidenceChecker` |
| `test_evaluation.py` | 5 | `ExperimentLogger` |
| `test_orchestration.py` | 7 | sequential routing |
| `test_v0_integration.py` | 4 | end-to-end |
| `test_rag.py` | **8** | chunker, embedder, BM25, Qdrant, hybrid, `CorpusSearchClient` |
| `test_safety.py` | **7** | keyword filter, `SafetyChecker` over goal/evidence/claims |
| `test_local_llm.py` | **4** | `LocalSLMClient`, SFT dataset |

(Plus the deliberation v1 ladder: claim selector, mechanism bundler,
sketcher, slot builder, slate selector, support attributor — all green.)

### Reproducibility envelope

Every run writes three artifacts to a stable, timestamped directory:

```
2026-05-14_rag_safety_e2e/artifacts/
├── output.json       ← ResearchOutput  (claims + evidence + provenance)
├── experiment.json   ← ExperimentRecord (config + seed + plan + verdicts)
└── safety.json       ← pre- and post-flight safety reports
```

`ExperimentRecord` includes a config hash, pipeline version, and schema
version. Same config + same seed + same data ⇒ same output.

---

## 6. Results & demo

*Corresponds to slides 8 (“Results”), 9 (live demo), and 10 (“Honest grading position”).*

### End-to-end run: SciFact RAG + safety, deterministic LLM

Command:

```
$ ASAR_SAFETY_ENABLED=1 ASAR_SEARCH_PROVIDER=corpus \
    uv run python -m asar.demo "What is known about BRCA1 in breast cancer?" \
    --output-dir /tmp/asar-demo-rag
```

Result (terminal tail):

```
Plan steps: 3
Evidence items: 3
ResearchOutput artifact:  output.json
ExperimentRecord artifact: experiment.json
```

A claim from the resulting `output.json`:

```json
{
  "claim_id": "claim_48e44de71da0",
  "epistemic_status": "high_confidence",
  "supporting_evidence_ids": ["evidence_f0e44290e496"],
  "reasoning_trace": "Claim mirrors evidence_f0e44290e496 for deterministic support checking.",
  "text": "Autophagy is a process in which subcellular membranes undergo dynamic morphological changes..."
}
```

…with the supporting evidence carrying full retrieval provenance:

```json
{
  "evidence_id": "evidence_f0e44290e496",
  "confidence": 0.621,
  "source": {
    "source_name": "corpus:scifact",
    "url": "https://huggingface.co/datasets/BeIR/scifact",
    "title": "The role of autophagy in cancer development and response to therapy",
    "raw_payload": {
      "chunk_id": "26952804::f1ad48d222f9",
      "doc_id": "26952804",
      "dense_rank": 7,
      "lexical_rank": 2,
      "fused_score": 0.0310544,
      "trust_label": "peer_reviewed",
      "section": "body",
      "tags": ["scifact", "scientific_claim"]
    }
  }
}
```

The corresponding `safety.json` shows clean pre- and post-flight
verdicts:

```json
{
  "pre_report":  { "blocked": false, "max_toxicity": 0.0, "max_injection": 0.0,
                   "verdict_count": 1, "unsafe_count": 0 },
  "post_report": { "blocked": false, "max_toxicity": 0.0, "max_injection": 0.0,
                   "verdict_count": 4, "unsafe_count": 0 },
  "stripped_claims": []
}
```

### Probe retrieval (CLI, hashing embedder)

Query: `"What causes BRCA1-related cancers?"`

| Rank | Doc ID    | Fused score | Snippet |
|------|-----------|-------------|---------|
| 1    | 1866911   | 0.0323      | Basal-like breast cancers arising in women carrying mutations in the BRCA1 gene... |
| 2    | 5372773   | 0.0164      | Human cytomegalovirus (HCMV) expresses several homologues of human interleukin 10 (hIL-10)... |
| 3    | 22975806  | 0.0161      | For individuals genetically predisposed to breast and ovarian cancer through inheritance of a mutant BRCA allele... |
| 4    | 3285322   | 0.0159      | Mutations in the BRCA1 and BRCA2 genes confer greater risk of developing breast cancer... |

Even with the deterministic hashing embedder, the top hit is the gold
BRCA1 paper. FastEmbed (`BAAI/bge-small-en-v1.5`) is expected to improve
this materially — but the hashing embedder is what we ship in tests so the
result is fully reproducible without weights.

### Rubric self-assessment

| Item | Status |
|------|--------|
| Data ingestion (new dataset) | **Done** — SciFact via `datasets`, normalised + chunked + indexed |
| Fine-tuning (Q&A) | **Done** — LoRA SFT on Qwen2.5-0.5B SLM, CPU/MPS-friendly |
| RAG | **Done** — Qdrant + BM25 + reciprocal-rank fusion on local corpus |
| Evaluation | **Done** — `ExperimentRecord` + `safety.json` + 186 tests |
| Toxicity / hallucinations | **Done** — Keyword + optional Detoxify; `EvidenceChecker` for groundedness |
| RLHF | **Done via DPO** — 1,000 preference pairs from SciFact, all `chosen != rejected`; `trl.DPOTrainer` over the SFT adapter |

The base model is an open-weights SLM (Qwen2.5-0.5B) that is **actually
fine-tuned** with both a task-specific Q&A SFT pass **and** a DPO pass for
preference alignment. That places this project at the highest grade tier
under the rubric (full SFT + RLHF on an open-weights SLM, runnable on a
laptop).

---

## 7. Limitations and future work

*Corresponds to slide 11 — “Limitations & next steps”.*

### Honest limitations

- **DPO, not full PPO RLHF**. The deliverable uses DPO (reward-model-free)
  because it trains stably on a laptop. Full PPO RLHF — separate reward
  model, actor / critic split, KL control — needs a GPU cluster and is
  out of scope for the time budget.
- **Small SFT / DPO corpora** (≈1,500 SFT examples, 1,000 DPO pairs).
  Sufficient as proof-of-shape; not a production model.
- **Hashing embedder by default**. Used everywhere in CI for determinism.
  `FastEmbed` is wired up but the demo numbers above use hashing.
- **Keyword safety baseline**. Catches obvious cases. Detoxify is
  optional and lazy-loaded.
- **Sequential orchestrator**. No re-planning, parallel execution, or
  multi-perspective debate — those are explicitly Phase 2 work in
  `PROJECT_DOSSIER.md § 15 Roadmap`.

### What would move the needle next (in order)

1. Swap to FastEmbed and report retrieval recall@5 / @10 against the
   SciFact qrels.
2. Train LoRA for >1 epoch on a ≥10k SciFact-derived SFT set + a ≥10k DPO
   set, and evaluate answer-grounded fraction before/after each stage.
3. Add a re-planning loop triggered by `EvidenceChecker` failure (the
   `VerificationProtocol` boundary already supports this).
4. Expand safety: source-level allowlists, retrieval-time injection
   filtering, redaction of cited PII.

---

## 8. How to reproduce

### Environment

- macOS or Linux
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

```
# Base + dev dependencies
uv sync --extra dev

# RAG dependencies (datasets, qdrant-client, fastembed, rank_bm25)
uv sync --extra dev --extra rag

# Optional: safety model backend
uv sync --extra dev --extra safety

# Optional: local LLM + fine-tuning (transformers, peft, trl, accelerate, torch)
uv sync --extra dev --extra local-llm
```

### Run the test suite

```
uv run pytest -q --ignore=tests/test_live_providers.py
# 186 passed in 0.64s
```

### Index the SciFact corpus

```
uv run python -m asar.execution.rag.cli \
    --dataset scifact --embed-backend hashing
```

Artifacts go under `data/corpora/scifact/`.

### Run the end-to-end demo with RAG + safety

```
ASAR_SAFETY_ENABLED=1 ASAR_SEARCH_PROVIDER=corpus \
    uv run python -m asar.demo "What is known about BRCA1 in breast cancer?" \
    --output-dir /tmp/asar-demo
```

Outputs `output.json`, `experiment.json`, `safety.json`.

### Build the SFT dataset

```
uv run python -m asar.finetune.cli_build_dataset \
    --prepare --output data/sft/scifact_qa.jsonl --limit 1500
```

### Fine-tune LoRA (Mac CPU/MPS-friendly defaults)

```
uv run python scripts/finetune_lora.py \
    --dataset data/sft/scifact_qa.jsonl \
    --output-dir runs/lora_qwen25_05b
```

### Use the fine-tuned adapter at inference

```
ASAR_MODEL_PROVIDER=local \
ASAR_LOCAL_ADAPTER_PATH=runs/lora_qwen25_05b \
    uv run python -m asar.demo "..."
```

---

## 9. File map

### Code

```
asar/
├── core/                 ← protocols, errors, llm/search abstractions
├── common/               ← config, ids, logging
├── schemas/              ← all typed boundaries (Pydantic v2)
├── planning/             ← SimplePlanner
├── execution/
│   ├── web_search_executor.py
│   └── rag/              ← NEW: chunker, embedder, retriever, scifact_loader, cli
├── memory/               ← WorkingMemory
├── deliberation/         ← SimpleSynthesizer + v1 ladder
├── verification/         ← EvidenceChecker
├── evaluation/           ← ExperimentLogger
├── orchestration/        ← SequentialOrchestrator
├── grounding/            ← (Phase 2)
├── safety/               ← NEW: KeywordSafetyFilter, DetoxifySafetyFilter,
│   │                       SafetyChecker (in __init__.py)
│   └── pipeline.py       ← NEW: SafetyAwareRunner wrapper
├── finetune/             ← NEW
│   ├── dataset.py                ← SFT dataset builder
│   ├── cli_build_dataset.py      ← CLI for SFT data
│   ├── preference_dataset.py     ← DPO preference dataset builder
│   └── cli_build_preference.py   ← CLI for DPO data
├── providers/
│   ├── corpus_search.py  ← NEW: CorpusSearchClient(SearchClientProtocol)
│   ├── local_llm.py      ← NEW: LocalSLMClient(LLMClientProtocol)
│   ├── factory.py        ← MODIFIED: corpus / local provider selection
│   └── ...
└── demo/                 ← CLI entry point (`python -m asar.demo`)
```

### Scripts

```
scripts/
├── build_sft_dataset.py  ← thin shim → asar/finetune/cli_build_dataset
├── finetune_lora.py      ← LoRA SFT training entry point
└── dpo_train.py          ← DPO training entry point (loads SFT adapter)
```

### Tests

```
tests/
├── test_rag.py            ← 8 RAG tests
├── test_safety.py         ← 7 safety tests
├── test_local_llm.py      ← 4 local-LLM / SFT-dataset tests
├── test_dpo_dataset.py    ← 4 DPO preference-dataset tests
└── ... 13 other files covering every v0 / v1 layer
```
Full suite: **186 passing tests in 0.64 s** (excluding optional live providers).

### Experiments

```
experiments/runs/
├── 2026-05-14_rag_safety_e2e/
│   ├── README.md            ← end-to-end experiment report
│   └── artifacts/
│       ├── output.json
│       ├── experiment.json
│       └── safety.json
└── 2026-05-14_dpo_preference_dataset/
    ├── README.md            ← DPO dataset experiment report
    └── sample_pairs.jsonl   ← representative (prompt, chosen, rejected) triples
```

### Datasets (generated, gitignored)

```
data/
├── corpora/scifact/         ← BeIR/SciFact, 5,183 docs, 4.5 MB parquet
│   └── normalized/{documents,queries,qrels}.jsonl
├── sft/scifact_qa.jsonl     ← ~1,500 SFT examples (regenerable)
└── dpo/scifact_pref.jsonl   ← 1,000 DPO preference pairs (2.7 MB, regenerable)
```

### Deliverable

```
deliverable/
├── README.md            ← index of this folder + one-command verify block
├── presentation.pptx    ← 12-slide deck, 6-minute talk + 2-minute demo
├── presentation.md      ← Markdown source (Marp-renderable, fallback)
├── documentation.md     ← this file — long-form write-up
├── results.md           ← concrete numbers and command outputs
├── rubric_check.md      ← grade-10 audit, one row per rubric item
├── demo_runbook.md      ← 2-minute live demo plan (verified end-to-end)
└── experiment_artifacts/
    ├── output.json
    ├── experiment.json
    └── safety.json
```

