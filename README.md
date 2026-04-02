# ASAR — Agentic Structured Autonomous Researcher

Project Name: Agentic Structured Autonomous Researcher
Team name:
Team Members: Iepure Antoniu, Mogovan Jonathan, Mosnegutu Adrian, Mititean Christian, Mititean Adrian

A neuro-symbolic multi-step research agent. The architecture is broader, but the implemented and now frozen baseline is a v0 sequential vertical slice: one goal, one planner, one web/search executor, in-memory working memory, single-pass synthesis, deterministic verification, experiment logging, and a typed `ResearchOutput`.

---

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
