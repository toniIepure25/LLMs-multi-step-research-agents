# ASAR — Agentic Structured Autonomous Researcher

## Project Information

- **Project name:** ASAR — Agentic Structured Autonomous Researcher
- **Team name:** `Prompt Goblins`
- **Team members:** `Iepure Antoniu`, `Mogovan Jonathan`, `Mosnegutu Adrian`, `Mititean Christian`, `Mititean Adrian`

## Milestone 2

### 1. Dataset Selection

- **Selected dataset:** `BeIR/scifact`
- **Why this dataset:** it is useful for retrieval and grounding evaluation, it is small enough to integrate cleanly, it is easy to normalize into chunked documents, and its total download size is safely under the 2GB constraint.
- **Observed download size:** about `2.8 MB`

### 2. Chunking Strategy

- **Chunking approach:** document-aware chunking, not naive fixed-size only
- **Order of chunking:** heading/section split first, then paragraph grouping, then sentence fallback for oversized text, with overlap preserved
- **Default chunking configuration:**
  - target size: `450` tokens
  - max size: `650` tokens
  - overlap: `80` tokens
  - minimum chunk size: `120` tokens
- **Metadata preserved per chunk:** `doc_id`, `chunk_id`, `title`, `section`, `source_type`, `dataset_name`, `source_url/path`, `tags`, `trust_label`, token count, character count

### 3. Vector Database Choice

- **Chosen vector database:** `Qdrant`
- **Why Qdrant:** it has a simple local setup, stores metadata well, supports semantic search cleanly, and is a better first production-oriented fit for this repo than introducing a heavier database dependency.

### 4. Model Choices

- **Production embedding model:** `BAAI/bge-small-en-v1.5` through FastEmbed
- **Deterministic fallback model:** hashing embedder
- **Why two options:** FastEmbed is the intended real semantic backend, while the hashing embedder gives us a deterministic local fallback for smoke tests and constrained environments.

### 5. RAG Strategies

- **Implemented retrieval strategy:** hybrid retrieval
- **Components used:**
  - dense semantic retrieval from Qdrant
  - lexical retrieval with BM25
  - reciprocal-rank fusion for combining results
- **Why this strategy:** it is stronger than dense-only retrieval in a clean first pass, while still staying simple enough to integrate without redesigning the application.

### 6. Architecture / Integration Summary

- The application keeps its existing typed flow:
  - `planning -> execution -> memory -> deliberation -> verification -> evaluation`
- The RAG subsystem is integrated inside the current execution/search boundary, not as a disconnected demo.
- Retrieved corpus chunks are normalized back into the app's existing `EvidenceItem` format, so the rest of the pipeline remains intact.

### 7. Assignment Documents

- **Technical design document:** [rag_dataset_chunking_vector_db_strategy.md](docs/rag_dataset_chunking_vector_db_strategy.md)
- **Async progress document:** [llm_assignment_progress.md](docs/llm_assignment_progress.md)

---

### Short Project Description

ASAR is a modular research and evidence-grounding application built around a
typed multi-step pipeline:

`planning -> execution -> memory -> deliberation -> verification -> evaluation`

The repo now also includes a first real corpus-backed RAG subsystem that fits
the existing architecture instead of bypassing it. The RAG path adds:

- dataset selection and download
- document normalization
- document-aware chunking
- vector indexing in Qdrant
- hybrid retrieval
- normalization of retrieved chunks back into the existing `EvidenceItem` flow

### Architecture At A Glance

- **Planner:** decomposes a question into typed retrieval steps
- **Execution layer:** retrieves evidence from web search or a local indexed corpus
- **Memory:** stores typed evidence artifacts
- **Deliberation:** synthesizes evidence into candidate claims / decisions
- **Verification:** checks claim support deterministically against evidence
- **Evaluation:** logs metrics and experiment artifacts

### RAG Decisions Implemented

- **Dataset selected:** `BeIR/scifact`
- **Why:** small, useful for retrieval/grounding, easy to normalize, under the 2GB limit
- **Chunking strategy:** section-aware -> paragraph-aware -> token-bounded with overlap
- **Vector DB:** Qdrant
- **Embedding models:** production `BAAI/bge-small-en-v1.5` via FastEmbed, deterministic fallback hashing embedder for smoke/CI
- **Retrieval strategy:** hybrid dense + BM25 with reciprocal-rank fusion

### Architecture Summary

- **Planning:** converts the user question into typed retrieval steps
- **Execution:** retrieves evidence from web search or the local RAG corpus
- **Memory:** stores typed evidence artifacts
- **Deliberation:** synthesizes evidence into claims and decisions
- **Verification:** checks whether final claims are supported by retrieved evidence
- **Evaluation:** logs metrics and experiment artifacts

A neuro-symbolic multi-step research agent. The architecture is broader, but the implemented and now frozen baseline is a v0 sequential vertical slice: one goal, one planner, one web/search executor, in-memory working memory, single-pass synthesis, deterministic verification, experiment logging, and a typed `ResearchOutput`.

## Read This First

If you are a **coding agent** entering this repo for the first time, read these files in this order:

| Order | File                                                                         | What you learn                                                                |
| ----- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1     | [AGENTS.md](AGENTS.md)                                                       | How to work in this repo — rules, workflows, pitfalls                         |
| 2     | [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md)                                     | Why this project exists, what the invariants are, how the layers fit together |
| 3     | [docs/architecture/system-overview.md](docs/architecture/system-overview.md) | Layer contracts — inputs, outputs, invariants per layer                       |
| 4     | [docs/architecture/component-map.md](docs/architecture/component-map.md)     | Where code lives, which schemas flow where                                    |
| 5     | [schemas/](schemas/)                                                         | The typed data structures — read these before writing any code                |
| 6     | [tasks/next_steps.md](tasks/next_steps.md)                                   | What to work on next                                                          |

If you are a **human collaborator**, the same order works. You can skip AGENTS.md if you prefer your own workflow.

---

## What This Is

ASAR is a research-grade framework for building multi-step autonomous research agents that go beyond naive prompt chaining. The core thesis: LLMs handle interpretation and reasoning; structured memory handles continuity; symbolic structures handle factual grounding; verification layers enforce constraints.

The full architecture includes grounding, richer memory, re-planning, and parallelism, but those are not part of the frozen v0 implementation target.

See [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md) for the full mission, design philosophy, and roadmap.

## Current Status

- v0 is frozen for now
- Frozen historical v0 baseline: [experiments/notes/v0_tier1_eval_set_004.md](experiments/notes/v0_tier1_eval_set_004.md)
- Active experimental v1-minimal baseline: [experiments/notes/v1_tier1_eval_set_004.md](experiments/notes/v1_tier1_eval_set_004.md)
- v1.1 grounded selection remains exploratory only and was not promoted after the focused 2008 live probes: [experiments/notes/v1_1_2008_probe_001.md](experiments/notes/v1_1_2008_probe_001.md), [experiments/notes/v1_1_2008_probe_002.md](experiments/notes/v1_1_2008_probe_002.md)
- v1.2 mechanism bundling remains exploratory only and was not promoted after the focused 2008, Great Depression, and dot-com live probes: [experiments/notes/v1_2_2008_probe_002.md](experiments/notes/v1_2_2008_probe_002.md), [experiments/notes/v1_2_great_depression_probe_001.md](experiments/notes/v1_2_great_depression_probe_001.md), [experiments/notes/v1_2_dotcom_probe_001.md](experiments/notes/v1_2_dotcom_probe_001.md)
- v1.3 mechanism sketching remains exploratory only and was not promoted after the focused 2008 live probe: [experiments/notes/v1_3_2008_probe_001.md](experiments/notes/v1_3_2008_probe_001.md)
- v1.4 slot-grounded drafting remains exploratory only and was not promoted after the focused 2008 live probe: [experiments/notes/v1_4_2008_probe_001.md](experiments/notes/v1_4_2008_probe_001.md)
- v0 tuning is complete and should remain frozen
- v1-minimal tuning is paused at the current baseline and remains the active runtime comparison point
- v1.1, v1.2, v1.3, and v1.4 tuning should also stop for now; future work should begin with a new consciously scoped design step rather than more narrow probe loops on any exploratory branch

See [docs/architecture/v0-canonical-architecture.md](docs/architecture/v0-canonical-architecture.md) for the frozen v0 scope, [docs/architecture/v1-minimal-architecture.md](docs/architecture/v1-minimal-architecture.md) for the active v1-minimal baseline status, [docs/architecture/v1_1-grounded-selection-architecture.md](docs/architecture/v1_1-grounded-selection-architecture.md) plus [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md) for the exploratory-only v1.1 outcome, [docs/architecture/v1_2-mechanism-bundling-architecture.md](docs/architecture/v1_2-mechanism-bundling-architecture.md) plus [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md) for the exploratory-only v1.2 outcome, [docs/architecture/v1_3-mechanism-sketching-architecture.md](docs/architecture/v1_3-mechanism-sketching-architecture.md) plus [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md) for the exploratory-only v1.3 outcome, and [docs/architecture/v1_4-slot-grounded-drafting-architecture.md](docs/architecture/v1_4-slot-grounded-drafting-architecture.md) plus [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md) for the exploratory-only v1.4 outcome.

## Why It Exists

Current LLM-based research agents suffer from:

- **No planning discipline** — linear execution without structured decomposition
- **No memory architecture** — context windows are the only "memory"
- **No verification** — outputs accepted uncritically
- **No reproducibility** — runs not logged, compared, or evaluated
- **No separation of concerns** — generation, verification, and planning entangled

See [PROJECT_DOSSIER.md § Non-Goals](PROJECT_DOSSIER.md#9-non-goals) for what this project explicitly avoids.

## Repository Structure

```
├── README.md                  # This file — entry point and reading order
├── PROJECT_DOSSIER.md         # Mission, architecture, invariants, roadmap
├── AGENTS.md                  # Operating manual for coding agents
├── pyproject.toml             # Python project configuration
│
├── config/                    # Machine-readable configuration (TOML)
│   ├── project.toml           #   Project metadata
│   ├── models.toml            #   LLM provider/model settings
│   ├── pipeline.toml          #   Layer enable/disable toggles
│   └── experiments.toml       #   Experiment defaults
│
├── schemas/                   # Canonical typed data structures (Pydantic)
│   ├── research_plan.py       #   ResearchPlan, PlanStep
│   ├── task_packet.py         #   TaskPacket, TaskStatus
│   ├── evidence_item.py       #   EvidenceItem, SourceMetadata
│   ├── citation_record.py     #   CitationRecord (Phase 2)
│   ├── decision_packet.py     #   DecisionPacket, Claim, EpistemicStatus
│   ├── verification_result.py #   VerificationResult, ClaimVerification, ClaimVerdict
│   ├── research_output.py     #   ResearchOutput — final pipeline artifact
│   └── experiment_record.py   #   ExperimentRecord
│
├── asar/                      # Source code — one subpackage per layer (import asar)
│   ├── core/                  #   Protocols and base types (no implementations)
│   ├── planning/              #   v0: SimplePlanner
│   ├── execution/             #   v0: WebSearchExecutor
│   ├── memory/                #   v0: WorkingMemory
│   ├── deliberation/          #   v0: SimpleSynthesizer
│   ├── grounding/             #   Phase 2: evidence normalization / citations
│   ├── verification/          #   v0: EvidenceChecker
│   ├── evaluation/            #   v0: ExperimentLogger
│   ├── orchestration/         #   v0: SequentialOrchestrator
│   ├── demo/                  #   Local mock/live demo wiring
│   ├── providers/             #   Concrete provider adapters behind typed boundaries
│   └── common/                #   Config loading, logging, ID generation
│
├── docs/
│   ├── architecture/          #   System design (overview, components, dataflow, decisions)
│   ├── research/              #   Research agenda, hypotheses, open questions
│   ├── evaluation/            #   Evaluation plan, benchmark definitions
│   └── operations/            #   Dev workflow, reproducibility protocol
│
├── experiments/               # Experiment tracking
│   ├── registry/              #   Index of all experiments
│   ├── templates/             #   Templates for experiments, ablations, error analysis, failed directions
│   ├── runs/                  #   Individual experiment run data
│   ├── notes/                 #   Freeform research notes
│   └── results/               #   Aggregated results
│
├── tasks/                     # Task tracking and roadmap
│   ├── next_steps.md          #   Immediate priorities
│   ├── backlog.md             #   Unprioritized work
│   └── phase_00_bootstrap.md  #   Phase 0 completion record
│
└── tests/                     # Test suite (mirrors asar/ structure)
```

## Getting Started

```bash
# Canonical local setup: Python 3.11, uv
git clone <repo-url> && cd asar
uv python install 3.11
uv sync --extra dev
uv run pytest
```

The repository includes a root [`.python-version`](/home/tonystark/Desktop/multi-step-agent-research/.python-version) file and targets Python 3.11+ throughout tooling and docs. Validation observed under Python 3.10.x is non-canonical and should not be treated as support.

## Running The Local Demo

```bash
uv run python -m asar.demo "What were the main causes of the 2008 financial crisis?"
```

By default the demo uses the real frozen v0 pipeline wired to deterministic local mock LLM and search clients. It writes run artifacts under `experiments/runs/` unless you override the output directory:

```bash
uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --output-dir /tmp/asar-demo
```

The command prints the `output.json` and `experiment.json` paths so the run can be inspected manually.

## Running A Live v0 Demo

The current live v0 path keeps the architecture unchanged and adds exactly one live provider choice per boundary:

- LLM: OpenAI
- Search: Tavily

Required environment variables:

```bash
export OPENAI_API_KEY=...
export ASAR_MODEL_PROVIDER=openai
export ASAR_MODEL_MODEL="llama3.3:70b"
export ASAR_OPENAI_BASE_URL="https://inference.ccrolabs.com/v1"

export TAVILY_API_KEY=...
export ASAR_SEARCH_PROVIDER=tavily
```

Live run command:

```bash
uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --mode live
```

Optional environment variables:

```bash
export ASAR_SEARCH_PROVIDER=tavily
```

The live LLM path uses the existing OpenAI-compatible adapter against the custom base URL above. If credentials are missing or the configured provider/base URL is unsupported, the live path fails clearly with an explanatory message and leaves the deterministic mock mode available via `--mode mock`.

## Corpus-Backed RAG Backend

The execution layer now also has an optional corpus-backed RAG backend. It does
not change the pipeline shape: the corpus retriever still normalizes retrieved
chunks into the existing `EvidenceItem` flow through `WebSearchExecutor`.

Bootstrap the first local corpus:

```bash
uv run python -m asar.execution.rag.bootstrap \
  --dataset scifact \
  --corpus-root data/corpora
```

For local smoke tests or constrained environments, the bootstrap also supports a
deterministic hashing embedder:

```bash
uv run python -m asar.execution.rag.bootstrap \
  --dataset scifact \
  --corpus-root data/corpora \
  --embed-backend hashing \
  --hash-dimension 256
```

Then point the live search provider at the indexed corpus:

```bash
export ASAR_SEARCH_PROVIDER=corpus
export ASAR_CORPUS_ROOT=data/corpora
export ASAR_CORPUS_DATASET=scifact
export ASAR_RAG_EMBED_BACKEND=fastembed
export ASAR_RAG_EMBED_MODEL=BAAI/bge-small-en-v1.5
```

See [rag_dataset_chunking_vector_db_strategy.md](docs/rag_dataset_chunking_vector_db_strategy.md)
for the dataset choice, chunking policy, vector DB decision, and current
limitations.

See [docs/operations/dev-workflow.md](docs/operations/dev-workflow.md) for the full development guide.

## Project Maturity

**Phase 0 — Bootstrap** (done). Documentation, typed schemas, protocol definitions, and experiment infrastructure are in place.

**Phase 1 — v0 Minimal Pipeline** (implemented and frozen). The frozen scope is: `SimplePlanner`, `WebSearchExecutor`, `WorkingMemory`, `SimpleSynthesizer`, `EvidenceChecker`, `ExperimentLogger`, and `SequentialOrchestrator`. It exercises six protocol layers plus the orchestration coordinator, stays sequential and single-goal, and produces a typed `ResearchOutput`. The official live reference baseline is [experiments/notes/v0_tier1_eval_set_004.md](experiments/notes/v0_tier1_eval_set_004.md).

**Current active experimental step — v1 minimal.** The system now includes candidate claim generation plus deterministic support-aware claim selection. The current active live baseline is [experiments/notes/v1_tier1_eval_set_004.md](experiments/notes/v1_tier1_eval_set_004.md). See [docs/architecture/v1-minimal-architecture.md](docs/architecture/v1-minimal-architecture.md) for the architectural summary and [tasks/handoff/2026-03-20_v1_minimal_baseline_freeze.md](tasks/handoff/2026-03-20_v1_minimal_baseline_freeze.md) for the phase handoff.

**Exploratory follow-on — v1.1 grounded selection.** This was explored through mocked checkpoints and focused 2008 live probes, but it was not promoted because it did not beat the active v1-minimal baseline on the key 2008 criteria. See [docs/architecture/v1_1-grounded-selection-architecture.md](docs/architecture/v1_1-grounded-selection-architecture.md), [experiments/notes/v1_1_2008_probe_001.md](experiments/notes/v1_1_2008_probe_001.md), [experiments/notes/v1_1_2008_probe_002.md](experiments/notes/v1_1_2008_probe_002.md), and [tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md](tasks/handoff/2026-03-21_v1_1_exploratory_freeze.md).

**Exploratory follow-on — v1.2 mechanism bundling.** This was explored through mocked bundling checkpoints and focused live probes on 2008, Great Depression, and dot-com. It produced useful architectural evidence, especially on Great Depression mechanism diversity, but it was not promoted because it did not show clear overall superiority to the active v1-minimal baseline. See [docs/architecture/v1_2-mechanism-bundling-architecture.md](docs/architecture/v1_2-mechanism-bundling-architecture.md), [experiments/notes/v1_2_2008_probe_002.md](experiments/notes/v1_2_2008_probe_002.md), [experiments/notes/v1_2_great_depression_probe_001.md](experiments/notes/v1_2_great_depression_probe_001.md), [experiments/notes/v1_2_dotcom_probe_001.md](experiments/notes/v1_2_dotcom_probe_001.md), and [tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md](tasks/handoff/2026-03-25_v1_2_exploratory_freeze.md).

**Exploratory follow-on — v1.3 mechanism sketching.** This was explored through mocked sketch-first checkpoints and one focused live 2008 probe. The live run was viable, grounded, and had strong evidence utilization, but it did not beat the active v1-minimal 2008 baseline on mechanism quality: the explicit OTC-derivatives family disappeared and the mechanism mix became broader. The live probe also exposed an operational artifact-routing bug, where the run completed under the wrong output directory. `v1.3` therefore remains exploratory only and was not promoted. See [docs/architecture/v1_3-mechanism-sketching-architecture.md](docs/architecture/v1_3-mechanism-sketching-architecture.md), [experiments/notes/v1_3_2008_probe_001.md](experiments/notes/v1_3_2008_probe_001.md), and [tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md](tasks/handoff/2026-03-26_v1_3_exploratory_freeze.md).

**Exploratory follow-on — v1.4 slot-grounded drafting.** This was explored through mocked slot-preservation checkpoints and one focused live 2008 probe. The live run was viable, preserved OTC derivatives, and materially improved evidence utilization, but it still did not beat the active v1-minimal 2008 baseline on the promotion criteria: groundedness regressed, one claim verified as insufficient, and the final set duplicated the housing-finance family instead of improving third-family coverage. The live probe also reproduced the operational artifact-routing bug, where the run completed under the wrong output directory. `v1.4` therefore remains exploratory only and was not promoted. See [docs/architecture/v1_4-slot-grounded-drafting-architecture.md](docs/architecture/v1_4-slot-grounded-drafting-architecture.md), [experiments/notes/v1_4_2008_probe_001.md](experiments/notes/v1_4_2008_probe_001.md), and [tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md](tasks/handoff/2026-03-31_v1_4_exploratory_freeze.md).

The active runtime comparison point remains [experiments/notes/v1_tier1_eval_set_004.md](experiments/notes/v1_tier1_eval_set_004.md). The next phase should begin with a new consciously scoped architecture-design step rather than resuming `v1.1`, `v1.2`, `v1.3`, or `v1.4` by default.

See [PROJECT_DOSSIER.md § Roadmap](PROJECT_DOSSIER.md#15-roadmap) for the phase plan and [tasks/next_steps.md](tasks/next_steps.md) for the current transition tasks.
