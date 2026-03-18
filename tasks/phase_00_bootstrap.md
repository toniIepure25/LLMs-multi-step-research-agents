# Phase 0: Bootstrap

**Goal:** Create a solid project foundation that future agents and human collaborators can build on confidently.

**Status:** Complete

## Deliverables

- [x] Repository initialized
- [x] Directory structure created
- [x] README.md — project overview
- [x] PROJECT_DOSSIER.md — full context for agents and collaborators
- [x] AGENTS.md — operating manual for coding agents
- [x] Architecture documentation (system overview, component map, dataflow, decision log)
- [x] Research documentation (agenda, hypotheses, open questions)
- [x] Evaluation documentation (plan, benchmarks)
- [x] Operations documentation (dev workflow, reproducibility)
- [x] Experiment infrastructure (templates, registry, directory structure)
- [x] Configuration layer (project, models, pipeline, experiments)
- [x] Typed schemas (Pydantic models for all inter-layer types)
- [x] Source module skeleton with interface stubs
- [x] Task tracking (next steps, backlog, phase plans)
- [x] GitHub scaffolding (issue templates, PR template, contributing guide)
- [x] Python project configuration (pyproject.toml)

## Exit Criteria

- A new contributor (human or agent) can understand the project by reading README → PROJECT_DOSSIER → AGENTS.md
- All architectural layers have documented interfaces
- All inter-layer data types have typed schemas
- The experiment infrastructure is ready for first use
- The codebase installs and passes `pytest` (even if tests are minimal)

## Transition to Phase 1

Phase 1 begins with implementing the minimal pipeline. See `tasks/next_steps.md`.
