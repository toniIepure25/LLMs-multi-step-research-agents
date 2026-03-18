# ASAR — Agentic Structured Autonomous Researcher

A neuro-symbolic multi-step research agent. The architecture is broader, but the currently frozen implementation target is a v0 sequential vertical slice: one goal, one planner, one web/search executor, in-memory working memory, single-pass synthesis, deterministic verification, experiment logging, and a typed `ResearchOutput`.

---

## Read This First

If you are a **coding agent** entering this repo for the first time, read these files in this order:

| Order | File | What you learn |
|-------|------|---------------|
| 1 | [AGENTS.md](AGENTS.md) | How to work in this repo — rules, workflows, pitfalls |
| 2 | [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md) | Why this project exists, what the invariants are, how the layers fit together |
| 3 | [docs/architecture/system-overview.md](docs/architecture/system-overview.md) | Layer contracts — inputs, outputs, invariants per layer |
| 4 | [docs/architecture/component-map.md](docs/architecture/component-map.md) | Where code lives, which schemas flow where |
| 5 | [schemas/](schemas/) | The typed data structures — read these before writing any code |
| 6 | [tasks/next_steps.md](tasks/next_steps.md) | What to work on next |

If you are a **human collaborator**, the same order works. You can skip AGENTS.md if you prefer your own workflow.

---

## What This Is

ASAR is a research-grade framework for building multi-step autonomous research agents that go beyond naive prompt chaining. The core thesis: LLMs handle interpretation and reasoning; structured memory handles continuity; symbolic structures handle factual grounding; verification layers enforce constraints.

The full architecture includes grounding, richer memory, re-planning, and parallelism, but those are not part of the frozen v0 implementation target.

See [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md) for the full mission, design philosophy, and roadmap.

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
- Search: Brave Search

Required environment variables:

```bash
export OPENAI_API_KEY=...
export BRAVE_SEARCH_API_KEY=...
export ASAR_MODEL_PROVIDER=openai
export ASAR_MODEL_MODEL=gpt-5.2
```

Live run command:

```bash
uv run python -m asar.demo \
  "What were the main causes of the 2008 financial crisis?" \
  --mode live
```

Optional environment variables:

```bash
export ASAR_SEARCH_PROVIDER=brave
export ASAR_OPENAI_BASE_URL=...
export ASAR_BRAVE_SEARCH_COUNTRY=US
export ASAR_BRAVE_SEARCH_LANG=en
```

If credentials are missing or the configured provider is unsupported, the live path fails clearly with an explanatory message and leaves the deterministic mock mode available via `--mode mock`.

See [docs/operations/dev-workflow.md](docs/operations/dev-workflow.md) for the full development guide.

## Project Maturity

**Phase 0 — Bootstrap** (done). Documentation, typed schemas, protocol definitions, and experiment infrastructure are in place.

**Phase 1 — v0 Minimal Pipeline** (current target). The frozen scope is: `SimplePlanner`, `WebSearchExecutor`, `WorkingMemory`, `SimpleSynthesizer`, `EvidenceChecker`, `ExperimentLogger`, and `SequentialOrchestrator`. It exercises six protocol layers plus the orchestration coordinator, stays sequential and single-goal, and produces a typed `ResearchOutput`. Grounding, `CitationRecord` handling, re-planning, parallelism, debate, and advanced memory remain out of scope for v0.

See [PROJECT_DOSSIER.md § Roadmap](PROJECT_DOSSIER.md#15-roadmap) for the full phase plan and [tasks/next_steps.md](tasks/next_steps.md) for the v0 build order.
