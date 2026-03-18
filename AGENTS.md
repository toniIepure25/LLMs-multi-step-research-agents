# Agents Operating Manual

This is your operating manual. Read it fully before making changes. It tells you *how to work* in this repo. For *what the project is and why*, see [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md).

---

## Read This First

Read these files in this exact order before doing anything:

| Order | File | You learn |
|-------|------|----------|
| **1** | **This file** | How to work here — rules, workflows, pitfalls |
| **2** | [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md) | Mission, invariants, layer responsibilities, terminology |
| **3** | [docs/architecture/system-overview.md](docs/architecture/system-overview.md) | Layer contracts — inputs, outputs, per-layer invariants |
| **4** | [docs/architecture/component-map.md](docs/architecture/component-map.md) | What code lives where, which schemas flow between which layers |
| **5** | [schemas/](schemas/) | The typed data structures — read before writing any code |
| **6** | [tasks/next_steps.md](tasks/next_steps.md) | What to work on now |

After reading these six files, you have enough context to contribute.

## Runtime Baseline

- Supported development and runtime target: **Python 3.11+**
- If you observe validation passing under Python 3.10.x, treat that as **non-canonical**. The repository contract is still Python 3.11+ as declared in `pyproject.toml`.
- When in doubt, align docs, tests, and implementation choices to the Python 3.11+ baseline.

## Frozen v0 Decisions

Until Phase 1 foundations are implemented, treat the following as frozen:

- Package name is `asar`
- Canonical layer names are `planning`, `execution`, `memory`, `deliberation`, `verification`, `evaluation`, `orchestration`, and `grounding`
- Current implementation target is the v0 sequential vertical slice:
  `SimplePlanner` → `WebSearchExecutor` → `WorkingMemory` → `SimpleSynthesizer` → `EvidenceChecker` → `ExperimentLogger` → `SequentialOrchestrator`
- `ResearchOutput` is part of v0
- `VerificationProtocol.verify()` returns `VerificationResult` and does not mutate claims
- `grounding` and `CitationRecord`-heavy citation handling are postponed to Phase 2
- v0 has no re-planning loop, no parallel execution, no multi-perspective debate, and no advanced memory compression

## How to Explore the Repo

```
# Structure
tree -L 2 -d

# Types (read these before writing code)
ls schemas/

# Architecture
cat docs/architecture/system-overview.md

# Current priorities
cat tasks/next_steps.md

# What's been decided
cat docs/architecture/decision-log.md

# What's unknown
cat docs/research/open-questions.md
```

---

## Repository Invariants

These are defined in [PROJECT_DOSSIER.md § Invariants](PROJECT_DOSSIER.md#10-invariants) and are **non-negotiable**. Every change you make must preserve all of them:

1. **Grounded output** — every claim traces to an `EvidenceItem`
2. **Typed boundaries** — all inter-layer data uses `schemas/` models, no raw strings
3. **Reproducible experiments** — config + seed + data = same result
4. **Generation ≠ verification** — the producer of a claim is never its sole checker
5. **Explicit memory tiers** — working / compressed / evicted is always queryable
6. **Swappable modules** — implementations replaceable if protocol contracts hold
7. **Orchestration is the only router** — layers never import each other directly

If your change would violate an invariant, you must first propose an amendment via the architecture decision process (see below).

---

## What Not to Change Casually

Some parts of this repo are **load-bearing** — changing them has cascading effects. Do not modify these without reading the full dependency chain and recording a decision in [docs/architecture/decision-log.md](docs/architecture/decision-log.md):

| Artifact | Why it's sensitive | What depends on it |
|----------|-------------------|-------------------|
| `schemas/*.py` | Typed contracts between every layer | All `asar/` modules, all tests, component-map, dataflow docs |
| `asar/core/protocols.py` | Interface contracts for all layers | Every layer implementation, orchestration dispatch |
| `PROJECT_DOSSIER.md § Invariants` (§10) | Defines what must always be true | Every design and review decision |
| `config/pipeline.toml` | Controls which layers are active | Orchestration, experiment reproducibility |
| `docs/architecture/decision-log.md` | Records *why* things are the way they are | Future decision-making |

**Safe to change freely:** `tasks/`, `experiments/notes/`, `experiments/runs/`, `docs/research/open-questions.md`, module-internal implementation details that don't alter a protocol.

---

## Rules for Making Changes

### Before Writing Code
1. Read this file and [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md)
2. Identify which layer(s) your change affects — see [docs/architecture/component-map.md](docs/architecture/component-map.md)
3. Check if a schema already exists in `schemas/` for your data types
4. Check if a protocol already exists in `asar/core/protocols.py` for your module
5. Read the target module's `__init__.py` docstring for its responsibilities and TODOs

### While Writing Code
1. Use types from `schemas/` — never create parallel type systems
2. Follow existing code style in the module you're modifying
3. Type-annotate all public interfaces
4. Add `# TODO(agent): <context>` markers for incomplete work
5. Keep functions focused — one responsibility
6. No unstructured string passing between layers

### After Writing Code
1. Run the test suite: `uv run pytest` in a Python 3.11+ environment
2. Update documentation if you changed any interface (see table below)
3. Update [tasks/next_steps.md](tasks/next_steps.md) if you completed a listed task
4. Write a structured handoff note (see format below)

### Documentation Update Matrix

| When you change... | Update... |
|-------------------|-----------|
| A schema in `schemas/` | Schema docstrings + [component-map.md](docs/architecture/component-map.md) + any docs referencing that schema |
| A protocol in `asar/core/` | Protocol docstrings + [system-overview.md](docs/architecture/system-overview.md) + [component-map.md](docs/architecture/component-map.md) |
| A layer's behavior | Module `__init__.py` docstring + [system-overview.md](docs/architecture/system-overview.md) if contract changes |
| Architecture | [decision-log.md](docs/architecture/decision-log.md) + [PROJECT_DOSSIER.md](PROJECT_DOSSIER.md) if invariants change |
| Config format | Config file comments + [docs/operations/dev-workflow.md](docs/operations/dev-workflow.md) |
| Experiment infra | Templates in `experiments/templates/` + [docs/evaluation/](docs/evaluation/) |

---

## How to Propose Architecture Changes

Do NOT silently change architectural boundaries. Follow this process:

1. **Record the decision** in [docs/architecture/decision-log.md](docs/architecture/decision-log.md) using the ADR format:
   - Context: what prompted the change
   - Options considered: at least two, with tradeoffs
   - Decision: what you chose and why
   - Consequences: what this means for the codebase
2. **Flag invariant impact** — if the change affects any invariant in [PROJECT_DOSSIER.md § Invariants](PROJECT_DOSSIER.md#10-invariants), say so explicitly
3. **Implement only after** the decision is recorded
4. **Update** [component-map.md](docs/architecture/component-map.md) and [system-overview.md](docs/architecture/system-overview.md) to reflect the new state

---

## How to Propose an Experiment

Before running a non-trivial experiment:

1. Pick the right template from [experiments/templates/](experiments/templates/):
   - Standard experiment: [experiment_template.md](experiments/templates/experiment_template.md)
   - Ablation study: [ablation_template.md](experiments/templates/ablation_template.md)
   - Error analysis: [error_analysis_template.md](experiments/templates/error_analysis_template.md)
2. Copy the template to `experiments/runs/YYYY-MM-DD_<short-name>/`
3. Fill in **all metadata fields before running** — especially hypothesis, config, seed, and baseline
4. If the experiment tests a hypothesis from [docs/research/hypotheses.md](docs/research/hypotheses.md), reference it by ID (e.g., H-001)
5. Run the experiment
6. Record results — even if negative, *especially* if negative
7. Add an entry to [experiments/registry/experiment_index.md](experiments/registry/experiment_index.md)
8. If results change your understanding of the system, update [docs/research/open-questions.md](docs/research/open-questions.md)

---

## How to Record a Failed Direction

When you try an approach and it doesn't work, **record it** so future agents don't repeat it:

1. Copy [experiments/templates/failed_direction_template.md](experiments/templates/failed_direction_template.md) to `experiments/notes/YYYY-MM-DD_failed_<short-name>.md`
2. Fill in: what you tried, why you expected it to work, what actually happened, and why it failed
3. Include enough detail that a future agent can understand the failure without re-running the experiment
4. If the failure reveals a new open question, add it to [docs/research/open-questions.md](docs/research/open-questions.md)
5. If the failure invalidates a hypothesis, update its status in [docs/research/hypotheses.md](docs/research/hypotheses.md)

**The goal is not to avoid failures — it's to avoid repeated failures.**

---

## Workflow Summary

```
1. Read AGENTS.md (this file)
2. Read PROJECT_DOSSIER.md (invariants, layers, terminology)
3. Identify the task (check tasks/next_steps.md)
4. Identify affected layer(s) and module(s)
5. Read existing code in those modules
6. Check schemas/ for relevant types
7. Check docs/architecture/decision-log.md for relevant past decisions
8. Plan the change (record in decision-log.md if non-trivial)
9. Implement
10. Test (uv run pytest)
11. Update docs (see documentation update matrix above)
12. Write handoff note
```

---

## Commit Message Format

```
<type>(<scope>): <short description>

<body — what changed and why>

<footer — TODOs, blockers, or handoff notes>
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `experiment`, `schema`, `config`

**Scopes:** `planning`, `execution`, `memory`, `deliberation`, `verification`, `grounding`, `evaluation`, `orchestration`, `core`, `common`, `infra`

These scope names match the `asar/` subdirectory names exactly.

---

## Handoff Note Format

After completing a unit of work, leave a handoff note as a commit message footer or in `tasks/handoff/`:

```markdown
## Handoff: <brief title>

### What was done
- <changes made>

### What was NOT done
- <deferred items>

### Decisions made
- <choices and rationale>

### Open questions
- <things the next agent should consider>

### Suggested next steps
- <recommended actions, ordered>
```

---

## Common Pitfalls

- **Don't invent new types** when a schema already exists — check [schemas/](schemas/) first
- **Don't pass raw strings** between layers — use typed packets
- **Don't skip documentation** — undocumented changes create debt for future agents
- **Don't implement beyond the current phase** — see roadmap in [PROJECT_DOSSIER.md § Roadmap](PROJECT_DOSSIER.md#15-roadmap)
- **Don't hardcode model names or API keys** — use [config/](config/)
- **Don't merge without tests** — even stubs should have test stubs
- **Don't change schemas without updating the component map** — [docs/architecture/component-map.md](docs/architecture/component-map.md)
- **Don't re-explore a failed direction** without reading [experiments/notes/](experiments/notes/) first

---

## Naming Conventions

These names are used consistently across code, docs, schemas, and config:

| Canonical name | Used as | Found in |
|---------------|---------|----------|
| `planning` | module name, commit scope, layer name | `asar/planning/`, docs, config |
| `execution` | module name, commit scope, layer name | `asar/execution/`, docs, config |
| `memory` | module name, commit scope, layer name | `asar/memory/`, docs, config |
| `deliberation` | module name, commit scope, layer name | `asar/deliberation/`, docs, config |
| `verification` | module name, commit scope, layer name | `asar/verification/`, docs, config |
| `grounding` | module name, commit scope, layer name | `asar/grounding/`, docs, config |
| `evaluation` | module name, commit scope, layer name | `asar/evaluation/`, docs, config |
| `orchestration` | module name, commit scope, layer name | `asar/orchestration/`, docs, config |
| `core` | module name, commit scope | `asar/core/` |
| `common` | module name, commit scope | `asar/common/` |

Schema type names (`ResearchPlan`, `TaskPacket`, `EvidenceItem`, `CitationRecord`, `DecisionPacket`, `VerificationResult`, `ResearchOutput`, `ExperimentRecord`) are PascalCase everywhere — code, docs, and diagrams.

Do not introduce alternative names. "Planner" means `asar/planning/`. "Evidence" means `EvidenceItem`. "Citation" means `CitationRecord`. "Verdict" means `ClaimVerification`.
